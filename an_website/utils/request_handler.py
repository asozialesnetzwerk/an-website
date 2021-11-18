# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
The base request handlers used for other modules.

This should only contain request handlers and the get_module_info function.
"""
from __future__ import annotations

import hashlib
import random
import re
import sys
import traceback
from datetime import datetime
from functools import cache
from typing import Optional, Union
from urllib.parse import quote, unquote

import orjson as json
from ansi2html import Ansi2HTMLConverter  # type: ignore

# pylint: disable=no-name-in-module
from Levenshtein import distance  # type: ignore
from tornado import httputil, web
from tornado.web import HTTPError, RequestHandler

from an_website.utils.utils import (
    REPO_URL,
    THEMES,
    ModuleInfo,
    add_args_to_url,
    bool_to_str,
    str_to_bool,
)

ip_hash_salt = [os.urandom(32), time.monotonic()]


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Utilitys",
        description="Nützliche Werkzeuge für alle möglichen Sachen.",
        handlers=(
            (r"/error/", ZeroDivision, {}),
            (r"/([1-5][0-9]{2}).html?", ErrorPage, {}),
        ),
        hidden=True,
    )


class BaseRequestHandler(RequestHandler):
    """The base tornado request handler used by every page."""

    RATELIMIT_NAME: str = "base"  # can be overridden in subclasses
    RATELIMIT_TOKENS: int = 1  # can be overridden in subclasses
    REQUIRES_AUTHORIZATION: bool = False  # can be overridden in subclasses

    # info about page, can be overridden in module_info
    title = "Das Asoziale Netzwerk"
    description = "Die tolle Webseite des Asozialen Netzwerkes"
    module_info: ModuleInfo

    def initialize(
        self,
        module_info: ModuleInfo,
        # default is true, because then empty args dicts are
        # enough to specify that the defaults should be used
        default_title: bool = True,
        default_description: bool = True,
    ):
        """
        Get title and description from the kwargs.

        If title and description are present in the kwargs they
        override self.title and self.description.
        """
        self.module_info: ModuleInfo = module_info
        if not default_title:
            self.title = self.module_info.get_page_info(self.request.path).name

        if not default_description:
            self.description = self.module_info.get_page_info(
                self.request.path
            ).description

    def data_received(self, chunk):
        """Do nothing."""

    def set_default_headers(self):
        """Opt out of all FLoC cohort calculation."""
        self.set_header("Permissions-Policy", "interest-cohort=()")

    async def prepare(self):  # pylint: disable=invalid-overridden-method
        """Check authorization and rate limits with redis."""
        if self.REQUIRES_AUTHORIZATION and not self.is_authorized():
            # TODO: self.set_header("WWW-Authenticate")
            raise HTTPError(401)

        if (
            # whether ratelimits are enabled
            self.settings.get("RATELIMITS")
            # ignore ratelimits in dev_mode
            and not sys.flags.dev_mode
            # ignore ratelimits for authorized requests
            and not self.is_authorized()
            # ignore Delimits for requests with method OPTIONS
            and not self.request.method == "OPTIONS"
        ):
            redis = self.settings.get("REDIS")
            prefix = self.settings.get("REDIS_PREFIX")
            tokens = getattr(
                self, "RATELIMIT_TOKENS_" + self.request.method, None
            )
            if tokens is None:
                tokens = self.RATELIMIT_TOKENS
            remote_ip = hashlib.sha1(
                self.request.remote_ip.encode("utf-8")
            ).hexdigest()
            result = await redis.execute_command(
                "CL.THROTTLE",
                f"{prefix}:ratelimit:{remote_ip}:{self.RATELIMIT_NAME}",
                15,  # max burst
                30,  # count per period
                60,  # period
                tokens,
            )
            self.set_header("X-RateLimit-Limit", result[1])
            self.set_header("X-RateLimit-Remaining", result[2])
            self.set_header("X-RateLimit-Reset", result[4])
            if result[0]:
                self.set_header("Retry-After", result[3])
                now = datetime.utcnow()
                if now.month == 4 and now.day == 20:
                    self.set_status(420, "Enhance Your Calm")
                    self.write_error(420)
                else:
                    self.set_status(429)
                    self.write_error(429)

    # pylint: disable=too-many-return-statements
    def get_error_page_description(self, status_code: int) -> str:
        """Get the description for the error page."""
        # see: https://developer.mozilla.org/docs/Web/HTTP/Status
        if 100 <= status_code < 199:
            return "Hier gibt es eine total wichtige Information."
        if 200 <= status_code < 299:
            return "Hier ist alles super! 🎶🎶"
        if 300 <= status_code <= 399:
            return "Eine Umleitung ist eingerichtet."
        if 400 <= status_code <= 499:
            if status_code == 404:
                return f"{self.request.path} wurde nicht gefunden."
            if status_code == 451:
                return "Hier wäre bestimmt geiler Scheiß."
            return "Ein Client-Fehler ist aufgetreten."
        if 500 <= status_code <= 599:
            return "Ein Server-Fehler ist aufgetreten."
        raise ValueError(
            f"{status_code} is not a valid HTTP response status code."
        )

    def write_error(self, status_code: int, **kwargs):
        """Render the error page with the status_code as a html page."""
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
            description=self.get_error_page_description(status_code),
        )

    def get_error_message(self, **kwargs):
        """
        Get the error message and return it.

        If the server_traceback setting is true (debug mode is activated)
        the traceback gets returned.
        """
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][:2])[-1]
        return self._reason

    def get_hashed_remote_ip(self) -> str:
        """Hash the remote ip and return it."""
        if ip_hash_salt[1] < time.monotonic() - (24 * 60 * 60):
            ip_hash_salt[0] = os.urandom(32)
            ip_hash_salt[1] = time.monotonic()
        return hashlib.sha1(
            self.request.remote_ip.encode("utf-8") + ip_hash_salt[0]
        ).hexdigest()

    @cache
    def fix_url(self, url: str, this_url: Optional[str] = None) -> str:
        """
        Fix a url and return it.

        If the url is from another website, link to it with the redirect page.
        Otherwise just return the url with no_3rd_party appended.
        """
        if this_url is None:
            # used for discord page
            this_url = self.request.full_url()

        if url.startswith("http") and f"//{self.request.host}" not in url:
            # url is to other website:
            url = f"/redirect/?to={quote(url)}&from={quote(this_url)}"

        url = add_args_to_url(
            url,
            # the no_3rd_party param:
            no_3rd_party=self.get_no_3rd_party()
            if self.get_no_3rd_party() != self.get_no_3rd_party_default()
            else None,
            # the theme param:
            theme=self.get_theme() if self.get_theme() != "default" else None,
        )

        if url.endswith("?"):
            url = url[:-1]

        if url.startswith("/"):
            # don't use relative urls
            protocol = None
            if self.request.host_name.endswith(".onion"):
                # if the host is an onion domain, use http
                protocol = self.settings["ONION_PROTOCOL"]
            elif self.settings.get("LINK_TO_HTTPS"):
                # always use https if the config is set
                protocol = "https"
            if protocol is None:
                # otherwise use the protocol of the request
                protocol = self.request.protocol

            if (
                "?" not in url
                and not url.endswith("/")
                and "." not in url.split("/")[-1]
            ):
                url += "/"
            return f"{protocol}://{self.request.host}{url}"

        return url

    def get_no_3rd_party_default(self) -> bool:
        """Get the default value for the no_3rd_party param."""
        return self.request.host_name.endswith(".onion")

    @cache
    def get_no_3rd_party(self) -> bool:
        """Return the no_3rd_party query argument as boolean."""
        default = self.get_no_3rd_party_default()
        no_3rd_party = self.get_request_var_as_bool(
            "no_3rd_party", default=default
        )
        return default if no_3rd_party is None else no_3rd_party

    @cache
    def get_theme(self):
        """Get the theme currently selected."""
        theme = self.get_request_var("theme", default=None)

        if theme in THEMES:
            return theme
        return "default"

    def get_display_theme(self):
        """Get the theme currently displayed."""
        theme = self.get_theme()

        if "random" not in theme:
            return theme

        # theme names to ignore:
        ignore_themes = ["random", "random-dark"]

        if theme == "random-dark":
            ignore_themes.append("light")

        return random.choice(
            tuple(_t for _t in THEMES if _t not in ignore_themes)
        )

    def get_form_appendix(self):
        """Get html to add to forms to keep important query args."""
        form_appendix: str

        if (
            "no_3rd_party" in self.request.query_arguments
            and self.get_no_3rd_party() != self.get_no_3rd_party_default()
        ):
            form_appendix = (
                f"<input name='no_3rd_party' class='hidden-input' "
                f"value='{bool_to_str(self.get_no_3rd_party())}'>"
            )
        else:
            form_appendix = ""

        if (
            "theme" in self.request.query_arguments
            and (theme := self.get_theme()) != "default"
        ):
            form_appendix += (
                f"<input name='theme' class='hidden-input' value='{theme}'>"
            )

        return form_appendix

    def get_contact_email(self) -> Optional[str]:
        """Get the contact email from the settings."""
        email = self.settings.get("CONTACT_EMAIL")
        if email is None:
            return None
        if not email.startswith("@"):
            return email
        # if mail starts with @ it is a catch all email
        return (
            self.request.path.replace("/", "-").strip("-") + "_contact" + email
        )

    def get_template_namespace(self):
        """
        Add useful things to the template namespace and return it.

        They are mostly needed by most of the pages (like title,
        description and no_3rd_party).
        """
        namespace = super().get_template_namespace()

        namespace.update(
            {
                "ansi2html": Ansi2HTMLConverter(inline=True, scheme="xterm"),
                "title": self.title,
                "description": self.description,
                "keywords": (
                    "Asoziales Netzwerk, Känguru-Chroniken"
                    + (
                        ""
                        if self.module_info is None
                        else ", "
                        + self.module_info.get_keywords_as_str(
                            self.request.path
                        )
                    )
                ),
                "no_3rd_party": self.get_no_3rd_party(),
                "lang": "de",  # can change in future
                "form_appendix": self.get_form_appendix(),
                "fix_url": self.fix_url,
                "REPO_URL": self.fix_url(REPO_URL),
                "theme": self.get_display_theme(),
                "contact_email": self.get_contact_email(),
                # this is not important because we don't need the templates
                # in a context without the request for soundboard and wiki
                "url": self.request.full_url(),
                "settings": self.settings,
            }
        )
        return namespace

    def get_request_var(
        self, name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the a value by name for the request.

        First try to get it as query argument, if that isn't present try to
        get the cookie with the name.
        """
        value = self.get_query_argument(name, default=None)

        if value is not None:
            return value

        value = self.get_cookie(name, default=None)
        if value is None:
            return default

        return value

    def get_request_var_as_bool(
        self, name: str, default: Optional[bool] = None
    ) -> Optional[bool]:
        """Get the a value by name as bool for the request."""
        value_str = self.get_request_var(name, default=None)
        if value_str is None:
            return default
        return str_to_bool(value_str, default=default)

    def get_argument(  # type: ignore[override]
        self,
        name: str,
        default: Union[
            None,
            str,
            web._ArgDefaultMarker,  # pylint: disable=protected-access
        ] = web._ARG_DEFAULT,  # pylint: disable=protected-access
        strip: bool = True,
    ) -> Optional[str]:
        """Get an argument based on body or query."""
        arg = super().get_argument(name, default=None, strip=strip)
        if arg is not None:
            return arg

        try:
            body = json.loads(self.request.body)
            if name in body:
                if strip:
                    return body[name].strip()
                return body[name]
        except json.JSONDecodeError:
            pass

        # pylint: disable=protected-access
        if isinstance(default, web._ArgDefaultMarker):
            raise web.MissingArgumentError(name)

        return default

    def is_authorized(self) -> bool:
        """Check whether the request is authorized."""
        api_secrets = self.settings.get("TRUSTED_API_SECRETS")

        if api_secrets is None or len(api_secrets) == 0:
            return False

        secret = self.request.headers.get("Authorization")

        if secret in api_secrets:
            return True
        # TODO: add some sort of UI to put the auth_key in the cookie
        secret = self.get_cookie("auth_key", default=None)

        return bool(secret in api_secrets)


class APIRequestHandler(BaseRequestHandler):
    """
    The base api request handler.

    It overrides the write error method to return errors as json.
    """

    ALLOWED_METHODS: tuple[str, ...] = ("GET",)

    def set_default_headers(self):
        """Set important default headers for the api request handlers."""
        super().set_default_headers()
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Max-Age
        # 7200 = 2h (the chromium max)
        self.set_header("Access-Control-Max-Age", "7200")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Content-Type
        self.set_header("Content-Type", "application/json")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Origin
        self.set_header("Access-Control-Allow-Origin", "*")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Headers
        self.set_header("Access-Control-Allow-Headers", "*")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Methods
        self.set_header(
            "Access-Control-Allow-Methods",
            ", ".join((*self.ALLOWED_METHODS, "OPTIONS")),
        )

    def write_error(self, status_code, **kwargs):
        """Finish with the status code and the reason as dict."""
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )

    def options(self, *args):  # pylint: disable=unused-argument
        """Handle OPTIONS requests."""
        # no body; only the default headers get used
        # `*args` is for route with `path arguments` supports
        self.set_status(204)
        self.finish()


class NotFound(BaseRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    RATELIMIT_TOKENS = 0

    def initialize(  # type: ignore # pylint: disable=arguments-differ
        self,
        # set default of module_info to none to not throw error
        module_info: ModuleInfo = None,
        **kwargs,
    ):
        """Do nothing to have default title and desc."""
        kwargs["module_info"] = module_info
        super().initialize(**kwargs)

    def get_protocol_and_host(self) -> str:
        """Get the beginning of the url."""
        return f"{self.request.protocol}://{self.request.host}"

    def get_query(self) -> str:
        """Get the query how you would add it to the end of the url."""
        if self.request.query == "":
            return ""  # if empty without question mark
        return f"?{self.request.query}"  # only add "?" if there is a query

    async def prepare(  # pylint: disable=too-many-branches  # noqa: C901
        self,
    ):
        """Throw a 404 http error or redirect to another page."""
        new_path = self.request.path.lower()
        if new_path.endswith("/index.html"):
            # len("index.html") = 10
            new_path = new_path[:-10]
        elif new_path.endswith("/index.htm"):
            # len("index.htm") = 9
            new_path = new_path[:-9]
        elif new_path.endswith(".html"):
            # len(".html") = 5
            new_path = new_path[:-5] + "/"
        elif new_path.endswith(".htm"):
            # len(".htm") = 4
            new_path = new_path[:-4] + "/"
        elif (
            # path already ends with a slash
            not new_path.endswith("/")
            # path is a file (has a . in the last part like "favicon.ico")
            and "." not in new_path.split("/")[-1]
        ):
            new_path += "/"

        if "//" in new_path:
            # replace multiple / with only one
            new_path = re.sub(r"/+", "/", new_path)
        if "_" in new_path:
            # replace underscore with minus
            new_path = new_path.replace("_", "-")

        if new_path != self.request.path:
            return self.redirect(
                self.get_protocol_and_host() + new_path + self.get_query(),
                True,
            )
        # "%20" → " "
        this_path = unquote(self.request.path)

        distances: list[tuple[int, str]] = []

        if len(this_path) < 4:
            # if /a/ redirect to / instead of /z/
            self.redirect(
                self.get_protocol_and_host() + "/" + self.get_query()
            )

        # prevent redirecting from /aa/ to /z/
        max_dist = min(4, len(this_path) - 3)

        for _mi in self.application.settings.get("MODULE_INFOS"):
            if _mi.path is not None:
                # get the smallest distance possible with the aliases
                dist = min(
                    distance(this_path, path)
                    for path in (*_mi.aliases, _mi.path)
                )
                if dist <= max_dist:
                    # only if the distance is less or equal then {max_dist}
                    distances.append((dist, _mi.path))
            if len(_mi.sub_pages) > 0:
                distances.extend(
                    (distance(this_path, _sp.path), _sp.path)
                    for _sp in _mi.sub_pages
                    if _sp.path is not None
                )

        if len(distances) > 0:
            # sort to get the one with the smallest distance in index 0
            distances.sort()
            dist, path = distances[0]
            if dist <= max_dist:
                # only if the distance is less or equal then {max_dist}
                return self.redirect(
                    self.get_protocol_and_host() + path + self.get_query(),
                    False,
                )

        raise HTTPError(404)


class ErrorPage(BaseRequestHandler):
    """A request handler that throws an error."""

    RATELIMIT_TOKENS = 0

    async def get(self, code: str):
        """Raise the error_code."""
        status_code: int = int(code)

        # get the reason
        reason: str = httputil.responses.get(status_code, "")

        # set the status code if tornado doesn't throw an error if it is set
        if status_code not in (204, 304) and not 100 <= status_code < 200:
            # set the status code
            self.set_status(status_code)

        return await self.render(
            "error.html",
            status=status_code,
            reason=reason,
            description=self.get_error_page_description(status_code),
        )


class ZeroDivision(BaseRequestHandler):
    """A fun request handler that throws an error."""

    RATELIMIT_TOKENS = 10

    async def prepare(self):
        """Divide by zero and throw an error."""
        if not self.request.method == "OPTIONS":
            await super().prepare()
            await self.finish(str(0 / 0))
