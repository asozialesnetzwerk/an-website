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

import logging
import random
import re
import sys
import time
import traceback
import uuid
from datetime import datetime
from functools import cache
from http.client import responses
from typing import Any
from urllib.parse import quote, unquote, urlparse, urlunparse

import elasticapm  # type: ignore
import orjson as json
from abydos.distance import Levenshtein  # type: ignore
from aioredis import Redis
from ansi2html import Ansi2HTMLConverter  # type: ignore
from blake3 import blake3  # type: ignore
from bs4 import BeautifulSoup
from elasticsearch import AsyncElasticsearch
from tornado import web
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError, MissingArgumentError, RequestHandler

from .. import REPO_URL
from .utils import (
    THEMES,
    ModuleInfo,
    add_args_to_url,
    bool_to_str,
    name_to_id,
    str_to_bool,
)

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Utilities",
        description="Nützliche Werkzeuge für alle möglichen Sachen.",
        handlers=(
            (r"/error/", ZeroDivision if sys.flags.dev_mode else NotFound, {}),
            (r"/([1-5][0-9]{2}).html?", ErrorPage, {}),
            (
                r"/@elastic/apm-rum@(.+)/dist/bundles"
                r"/elastic-apm-rum.umd(\.min|).js(\.map|)",
                ElasticRUM,
            ),
        ),
        hidden=True,
    )


# pylint: disable=too-many-public-methods
class BaseRequestHandler(RequestHandler):
    """The base Tornado request handler used by every page."""

    # can be overridden in subclasses
    REQUIRES_AUTHORIZATION: bool = False

    ELASTIC_RUM_JS_URL = (
        "/@elastic/apm-rum@^5/dist/bundles/elastic-apm-rum"
        f".umd{'.min' if not sys.flags.dev_mode else ''}.js"
    )

    module_info: ModuleInfo
    # info about page, can be overridden in module_info
    title = "Das Asoziale Netzwerk"
    short_title = "Das Asoziale Netzwerk"
    description = "Die tolle Webseite des Asozialen Netzwerkes"

    def initialize(
        self,
        *,
        module_info: ModuleInfo,
        # default is true, because then empty args dicts are
        # enough to specify that the defaults should be used
        default_title: bool = True,
        default_description: bool = True,
    ) -> None:
        """
        Get title and description from the kwargs.

        If title and description are present in the kwargs they
        override self.title and self.description.
        """
        self.module_info = module_info
        if not default_title:
            page_info = self.module_info.get_page_info(self.request.path)
            self.title = page_info.name
            self.short_title = page_info.short_name or self.title

        if not default_description:
            self.description = self.module_info.get_page_info(
                self.request.path
            ).description

    def data_received(self, chunk: Any) -> None:
        """Do nothing."""

    @property
    def redis(self) -> None | Redis:
        """Get the Redis client from the settings."""
        return self.settings.get("REDIS")

    @property
    def redis_prefix(self) -> str:
        """Get the Redis prefix from the settings."""
        return self.settings.get("REDIS_PREFIX", "")

    @property
    def elasticsearch(self) -> None | AsyncElasticsearch:
        """Get the Elasticsearch client from the settings."""
        return self.settings.get("ELASTICSEARCH")

    @property
    def elasticsearch_prefix(self) -> str:
        """Get the Elasticsearch prefix from the settings."""
        return self.settings.get("ELASTICSEARCH_PREFIX", "")

    @property
    def elastic_apm_client(self) -> None | elasticapm.Client:
        """Get the Elastic APM client from the settings."""
        return self.settings.get("ELASTIC_APM_CLIENT")

    def set_default_headers(self) -> None:
        """Set default headers."""
        # Opt out of all FLoC cohort calculation.
        self.set_header("Permissions-Policy", "interest-cohort=()")
        # community.torproject.org/onion-services/advanced/onion-location/
        if (
            _oa := self.settings.get("ONION_ADDRESS")
        ) and not self.request.host.endswith(".onion"):
            self.set_header(
                "Onion-Location",
                _oa
                + self.request.path
                + (f"?{self.request.query}" if self.request.query else ""),
            )

    async def prepare(  # pylint: disable=invalid-overridden-method
        self,
    ) -> None:
        """Check authorization and call self.ratelimit()."""
        if self.REQUIRES_AUTHORIZATION and not self.is_authorized():
            # TODO: self.set_header("WWW-Authenticate")
            raise HTTPError(401)

        if (_d := random.randint(0, 1337)) in {69, 420}:
            self.set_cookie("c", "s", expires_days=_d / 24, path="/")

        if not await self.ratelimit(True):
            await self.ratelimit()

    async def ratelimit(self, global_ratelimit: bool = False) -> bool:
        """Take b1nzy to space using Redis."""
        if (
            not self.settings.get("RATELIMITS")
            or self.request.method == "OPTIONS"
            or self.is_authorized()
        ):
            return False
        # pylint: disable=not-callable
        remote_ip = blake3(
            str(self.request.remote_ip).encode("ascii")
        ).hexdigest()
        if global_ratelimit:
            key = f"{self.redis_prefix}:ratelimit:{remote_ip}"
            max_burst = 99
            count_per_period = 20
            period = 1
            tokens = 10 if self.settings.get("UNDER_ATTACK") else 1
        else:
            bucket = getattr(
                self, f"RATELIMIT_{self.request.method}_BUCKET", ""
            )
            limit = getattr(self, f"RATELIMIT_{self.request.method}_LIMIT", 0)
            if not (bucket and limit):
                logger.debug(
                    "No ratelimit for path %s with method %s",
                    self.request.path,
                    self.request.method,
                )
                return False
            key = f"{self.redis_prefix}:ratelimit:{remote_ip}:{bucket}"
            max_burst = limit - 1
            count_per_period = getattr(
                self,
                f"RATELIMIT_{self.request.method}_COUNT_PER_PERIOD",
                1,
            )
            period = getattr(
                self, f"RATELIMIT_{self.request.method}_PERIOD", 1
            )
            tokens = 1
        # self.redis could be None
        # but it's better to complain loudly than to fail silently
        result = await self.redis.execute_command(  # type: ignore
            "CL.THROTTLE",
            key,
            max_burst,
            count_per_period,
            period,
            tokens,
        )
        if result[0]:
            retry_after = result[3] + 1  # redis-cell stupidly rounds down
            self.set_header("Retry-After", retry_after)
            if global_ratelimit:
                self.set_header("X-RateLimit-Global", "true")
        if not global_ratelimit:
            reset_after = result[4] + 1  # redis-cell stupidly rounds down
            self.set_header("X-RateLimit-Limit", result[1])
            self.set_header("X-RateLimit-Remaining", result[2])
            self.set_header("X-RateLimit-Reset", time.time() + reset_after)
            self.set_header("X-RateLimit-Reset-After", reset_after)
            self.set_header(
                "X-RateLimit-Bucket",
                # pylint: disable=not-callable
                blake3(bucket.encode("ascii")).hexdigest(),
            )
        if result[0]:
            now = datetime.utcnow()
            if now.month == 4 and now.day == 20:
                self.set_status(420)
                self.write_error(420)
            else:
                self.set_status(429)
                self.write_error(429)
        return bool(result[0])

    # pylint: disable=too-many-return-statements
    def get_error_page_description(self, status_code: int) -> str:
        """Get the description for the error page."""
        # see: https://developer.mozilla.org/docs/Web/HTTP/Status
        if 100 <= status_code <= 199:
            return "Hier gibt es eine total wichtige Information."
        if 200 <= status_code <= 299:
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

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Render the error page with the status_code as a HTML page."""
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
            description=self.get_error_page_description(status_code),
        )

    def get_error_message(self, **kwargs: dict[str, Any]) -> str:
        """
        Get the error message and return it.

        If the serve_traceback setting is true (debug mode is activated)
        the traceback gets returned.
        """
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError  # type: ignore
        ):
            if self.settings.get("serve_traceback") or self.is_authorized():
                return "".join(
                    traceback.format_exception(
                        *kwargs["exc_info"]  # type: ignore
                    )
                ).strip()
            return "".join(
                traceback.format_exception_only(
                    *kwargs["exc_info"][:2]  # type: ignore
                )
            ).strip()
        if "exc_info" in kwargs and isinstance(
            kwargs["exc_info"][1], MissingArgumentError  # type: ignore
        ):
            return kwargs["exc_info"][1].log_message  # type: ignore
        return str(self._reason)

    @cache
    def get_user_id(self) -> str:
        """Get the user id saved in the cookie or create one."""
        _user_id = self.get_secure_cookie("user_id", max_age_days=90)
        # TODO: ask for cookie consent
        user_id = (
            str(uuid.uuid4()) if _user_id is None else _user_id.decode("ascii")
        )
        # save it in cookie or reset expiry date
        self.set_secure_cookie(
            "user_id",
            user_id,
            expires_days=90,
            path="/",
            samesite="Strict",
        )
        return user_id

    def get_protocol(self) -> str:
        """Get scheme of the URL."""
        if self.request.host_name.endswith(".onion"):
            # if the host is an onion domain, use HTTP
            return self.settings["ONION_PROTOCOL"] or "http"
        if self.settings.get("LINK_TO_HTTPS"):
            # always use HTTPS if the config is set
            return "https"
        # otherwise use the protocol of the request
        return self.request.protocol

    def get_protocol_and_host(self) -> str:
        """Get the beginning of the URL."""
        return f"{self.get_protocol()}://{self.request.host}"

    def get_module_infos(self) -> tuple[ModuleInfo, ...]:
        """Get the module infos."""
        return self.settings.get("MODULE_INFOS") or tuple()

    @cache
    def fix_url(  # pylint: disable=too-many-arguments
        self,
        url: str,
        this_url: None | str = None,
        always_add_params: bool = False,
        force_absolute: bool = True,
        # to override them (used in the settings)
        theme: None | str = None,
        no_3rd_party: None | bool = None,
        dynload: None | bool = None,
    ) -> str:
        """
        Fix a URL and return it.

        If the URL is from another website, link to it with the redirect page.
        Otherwise just return the URL with no_3rd_party appended.
        """
        parsed_url = urlparse(url)

        if parsed_url.netloc and parsed_url.netloc != self.request.host:
            # URL is to other website:
            parsed_url = urlparse(
                f"/redirect/?to={quote(url)}"
                f"&from={quote(this_url or self.request.full_url())}"
            )
        host = parsed_url.netloc or self.request.host
        add_protocol_and_host = force_absolute or host != self.request.host

        if no_3rd_party is None:
            no_3rd_party = self.get_no_3rd_party()
        if theme is None:
            theme = self.get_theme()
        if dynload is None:
            dynload = self.get_dynload()

        return add_args_to_url(
            urlunparse(
                (
                    self.get_protocol() if add_protocol_and_host else "",
                    host if add_protocol_and_host else "",
                    parsed_url.path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            ),
            # the no_3rd_party param:
            no_3rd_party=no_3rd_party
            if always_add_params
            or no_3rd_party != self.get_saved_no_3rd_party()
            else None,
            # the theme param:
            theme=theme
            if always_add_params or theme != self.get_saved_theme()
            else None,
            # the dynload param:
            dynload=dynload
            if always_add_params or dynload != self.get_saved_dynload()
            else None,
        )

    def get_no_3rd_party_default(self) -> bool:
        """Get the default value for the no_3rd_party param."""
        return self.request.host_name.endswith(".onion")

    def get_saved_no_3rd_party(self) -> bool:
        """Get the saved value for no_3rd_party."""
        default = self.get_no_3rd_party_default()
        no_3rd_party = self.get_cookie("no_3rd_party")
        if no_3rd_party is None:
            return default
        return str_to_bool(no_3rd_party, default)

    @cache
    def get_no_3rd_party(self) -> bool:
        """Return the no_3rd_party query argument as boolean."""
        saved = self.get_saved_no_3rd_party()
        no_3rd_party = self.get_argument("no_3rd_party", default=None)
        if no_3rd_party is None:
            return saved
        return str_to_bool(no_3rd_party, saved)

    def get_saved_dynload(self) -> bool:
        """Get the saved value for dynload."""
        dynload = self.get_cookie("dynload")
        if dynload is None:
            return False
        return str_to_bool(dynload, False)

    def get_dynload(self) -> bool:
        """Return the dynload query argument as boolean."""
        saved = self.get_saved_dynload()
        dynload = self.get_argument("dynload", default=None)
        if dynload is None:
            return saved
        return str_to_bool(dynload, saved)

    def get_saved_theme(self) -> str:
        """Get the theme saved in the cookie."""
        theme = self.get_cookie("theme")
        if theme in THEMES:
            return theme
        return "default"

    @cache
    def get_theme(self) -> str:
        """Get the theme currently selected."""
        theme = self.get_argument("theme", default=None)
        if theme in THEMES:
            return theme
        return self.get_saved_theme()

    def get_display_theme(self) -> str:
        """Get the theme currently displayed."""
        theme = self.get_theme()

        if "random" not in theme:
            return theme

        # theme names to ignore:
        ignore_themes = ["random", "random-dark"]

        if theme == "random-dark":
            ignore_themes.extend(("light", "light-blue", "fun"))

        return random.choice(
            tuple(_t for _t in THEMES if _t not in ignore_themes)
        )

    def get_form_appendix(self) -> str:
        """Get HTML to add to forms to keep important query args."""
        form_appendix: str

        form_appendix = (
            f"<input name='no_3rd_party' class='hidden-input' "
            f"value='{bool_to_str(self.get_no_3rd_party())}'>"
            if "no_3rd_party" in self.request.query_arguments
            and self.get_no_3rd_party() != self.get_saved_no_3rd_party()
            else ""
        )

        if self.get_dynload() != self.get_saved_dynload():
            form_appendix += (
                f"<input name='dynload' class='hidden-input' "
                f"value='{bool_to_str(self.get_dynload())}'>"
            )

        if (theme := self.get_theme()) != self.get_saved_theme():
            form_appendix += (
                f"<input name='theme' class='hidden-input' value='{theme}'>"
            )

        return form_appendix

    def get_contact_email(self) -> None | str:
        """Get the contact email from the settings."""
        email = self.settings.get("CONTACT_EMAIL")
        if not email:
            return None
        email_str = str(email)
        if not email_str.startswith("@"):
            return email_str
        # if mail starts with @ it is a catch-all email
        return name_to_id(self.request.path) + "_contact" + email_str

    def get_template_namespace(self) -> dict[str, Any]:
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
                "short_title": self.short_title,
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
                "elastic_rum_js_url": self.ELASTIC_RUM_JS_URL,
                "url": self.request.full_url(),
                "settings": self.settings,
                "c": str_to_bool(self.get_cookie("c", "n"), False),
                "dynload": self.get_dynload(),
            }
        )
        return namespace

    def get_argument(  # type: ignore[override]
        self,
        name: str,
        default: (
            None | str | web._ArgDefaultMarker
        ) = web._ARG_DEFAULT,  # pylint: disable=protected-access
        strip: bool = True,
    ) -> None | str:
        """Get an argument based on body or query."""
        arg = super().get_argument(name, default=None, strip=strip)
        if arg is not None:
            return arg

        try:
            body = json.loads(self.request.body)
        except json.JSONDecodeError:
            pass
        else:
            if name in body:
                val = str(body[name])
                return val.strip() if strip else val

        # pylint: disable=protected-access
        if isinstance(default, web._ArgDefaultMarker):
            raise web.MissingArgumentError(name)

        return default

    def is_authorized(self) -> bool:
        """Check whether the request is authorized."""
        api_secrets = self.settings.get("TRUSTED_API_SECRETS")
        return bool(
            api_secrets  # api_secrets has to be truthy
            and (
                self.request.headers.get("Authorization") in api_secrets
                or self.get_argument("key", default=None) in api_secrets
                or self.get_cookie("key", default=None) in api_secrets
            )
        )


class APIRequestHandler(BaseRequestHandler):
    """
    The base API request handler.

    It overrides the write error method to return errors as JSON.
    """

    ALLOWED_METHODS: tuple[str, ...] = ("GET",)

    def set_default_headers(self) -> None:
        """Set important default headers for the API request handlers."""
        super().set_default_headers()
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Max-Age
        # 7200 = 2h (the chromium max)
        self.set_header("Access-Control-Max-Age", "7200")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Content-Type
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Origin
        self.set_header("Access-Control-Allow-Origin", "*")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Headers
        self.set_header("Access-Control-Allow-Headers", "*")
        # dev.mozilla.org/docs/Web/HTTP/Headers/Access-Control-Allow-Methods
        self.set_header(
            "Access-Control-Allow-Methods",
            ", ".join((*self.ALLOWED_METHODS, "OPTIONS")),
        )

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Finish with the status code and the reason as dict."""
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )

    def options(  # pylint: disable=unused-argument
        self, *args: list[Any]
    ) -> None:
        """Handle OPTIONS requests."""
        # no body; only the default headers get used
        # `*args` is for route with `path arguments` supports
        self.set_status(204)
        self.finish()


class NotFound(BaseRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    def initialize(  # type: ignore
        self, *args: list[Any], **kwargs: dict[str, Any]
    ) -> None:
        """Do nothing to have default title and desc."""
        if "module_info" not in kwargs:
            kwargs["module_info"] = None  # type: ignore
        super().initialize(*args, **kwargs)  # type: ignore

    def get_query(self) -> str:
        """Get the query how you would add it to the end of the URL."""
        if not self.request.query:
            return ""  # if empty without question mark
        return f"?{self.request.query}"  # only add "?" if there is a query

    async def prepare(  # pylint: disable=too-many-branches  # noqa: C901
        self,
    ) -> None:
        """Throw a 404 HTTP error or redirect to another page."""
        await super().prepare()
        new_path = self.request.path.lower()
        if new_path in {
            "/3.php",
            "/admin/controller/extension/extension/",
            "/assets/filemanager/dialog.php",
            "/assets/vendor/server/php/index.php",
            "/.aws/credentials/",
            "/aws.yml",
            "/.env",
            "/.env.bak",
            "/.ftpconfig",
            "/phpinfo.php",
            "/-profiler/phpinfo/",
            "/public/assets/jquery-file-upload/server/php/index.php",
            "/root.php",
            "/settings/aws.yml",
            "/uploads/",
            "/wordpress/",
            "/wp/",
            "/wp-admin",
            "/wp-admin/",
            "/wp-admin/css/",
            "/wp-includes",
            "/wp-includes/",
            "/wp-login",
            "/wp-login/",
            "/wp-login.php",
            "/wp-upload",
            "/wp-upload/",
            "/wp-upload.php",
        }:
            raise HTTPError(469)
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
            # path is a file (has a "." in the last part like "favicon.ico")
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
        this_path = unquote(self.request.path).strip("/")

        distances: list[tuple[float, str]] = []

        for _mi in self.get_module_infos():
            if _mi.path is not None:
                # get the smallest distance possible with the aliases
                dist = min(
                    Levenshtein().dist(this_path, path.strip("/"))
                    for path in (*_mi.aliases, _mi.path)
                    if path != "/z/"
                )
                if dist <= 0.5:
                    # only if the distance is less than or equal 0.5
                    distances.append((dist, _mi.path))
            if len(_mi.sub_pages) > 0:
                distances.extend(
                    (
                        Levenshtein().dist(this_path, _sp.path.strip("/")),
                        _sp.path,
                    )
                    for _sp in _mi.sub_pages
                    if _sp.path is not None
                )

        if len(distances) > 0:
            # sort to get the one with the smallest distance in index 0
            distances.sort()
            dist, path = distances[0]
            if dist <= 0.5:
                # only if the distance is less than or equal 0.5
                return self.redirect(
                    self.get_protocol_and_host() + path + self.get_query(),
                    False,
                )

        raise HTTPError(404)


class ErrorPage(BaseRequestHandler):
    """A request handler that throws an error."""

    async def get(self, code: str) -> None:
        """Raise the error_code."""
        status_code: int = int(code)

        # get the reason
        reason: str = responses.get(status_code, "")

        # set the status code if Tornado doesn't throw an error if it is set
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

    async def prepare(self) -> None:
        """Divide by zero and throw an error."""
        if not self.request.method == "OPTIONS":
            0 / 0  # pylint: disable=pointless-statement


class ElasticRUM(BaseRequestHandler):
    """A request handler that serves the RUM script."""

    URL = (
        "https://unpkg.com/@elastic/apm-rum@{}"
        "/dist/bundles/elastic-apm-rum.umd{}.js{}"
    )
    SCRIPTS: dict[str, tuple[str, float]] = {}

    async def get(self, version: str, spam: str = "", eggs: str = "") -> None:
        """Serve the RUM script."""
        key = version + spam + eggs
        if key not in self.SCRIPTS or self.SCRIPTS[key][1] < time.monotonic():
            response = await AsyncHTTPClient().fetch(
                self.URL.format(version, spam, eggs), raise_error=False
            )
            if response.code != 200:
                raise HTTPError(response.code, reason=response.reason)
            self.SCRIPTS[key] = (
                response.body.decode(),
                time.monotonic() + 365 * 60 * 60 * 24,
            )
            new_path = urlparse(response.effective_url).path
            if new_path.endswith(".js"):
                BaseRequestHandler.ELASTIC_RUM_JS_URL = new_path
            logger.info("RUM script %s updated", new_path)
            self.redirect(self.fix_url(new_path), False)
            return
        if eggs:
            self.set_header("Content-Type", "application/json")
        else:
            self.set_header("Content-Type", "application/javascript")
            if spam:
                self.set_header("SourceMap", self.URL + ".map")
        self.set_header(
            "Cache-Control", f"min-fresh={365 * 60 * 60 * 24}, immutable"
        )
        return await self.finish(self.SCRIPTS[key][0])


class JSONRequestHandler(APIRequestHandler):
    """A request handler that returns the page wrapped in JSON."""

    async def get(self, path: str) -> None:  # TODO: Improve this
        """Get the page wrapped in JSON and send it."""
        if path.startswith("/api/"):
            raise HTTPError(403)
        url = re.sub(
            r"^https?://[^/]+\.onion/",  # TODO: do this properly
            f"http://localhost:{self.settings.get('PORT')}/",
            self.fix_url(
                path
                + ("?" + self.request.query if self.request.query else ""),
                always_add_params=True,
            ),
        )

        response = await AsyncHTTPClient().fetch(
            url, raise_error=False, headers=self.request.headers
        )
        if response.code != 200:
            raise HTTPError(response.code, reason=response.reason)

        parsed_response_url = urlparse(response.effective_url)

        if parsed_response_url.netloc not in {
            "127.0.0.1",
            f"127.0.0.1:{self.settings.get('PORT')}" "localhost",
            f"localhost:{self.settings.get('PORT')}",
            self.request.host,
            self.request.host_name,
        }:
            return await self.finish(
                {  # TODO: Don't do the request for /chat/ or other known redir
                    "redirect": response.effective_url,
                }
            )

        soup = BeautifulSoup(response.body.decode("utf-8"), "html.parser")
        await self.finish(
            {
                "url": self.fix_url(
                    urlunparse(
                        (
                            self.request.protocol,
                            self.request.host,
                            *parsed_response_url[2:],
                        )
                    )
                ),
                "title": (soup.title.string if soup.title else ""),
                "body": "".join(
                    str(_el) for _el in soup.find_all(id="body")[0].contents
                ).strip(),  # ids are unique
                "scripts": [
                    {
                        "src": _s.get("src"),
                        "script": _s.string,
                        "onload": _s.get("onload"),
                    }
                    for _s in soup.find_all("script")
                    if "class" not in _s.attrs
                    or "on-every-page" not in _s["class"]
                ]
                if soup.head
                else [],
                "stylesheets": (
                    [
                        str(_s.get("href")).strip()
                        for _s in soup.find_all("link", rel="stylesheet")
                        if "class" not in _s.attrs
                        or "on-every-page" not in _s["class"]
                    ]
                )
                if soup.head
                else [],
                "css": "\n".join(
                    str(_s.string or "")
                    for _s in soup.find_all("style")
                    if "class" not in _s.attrs
                    or "on-every-page" not in _s["class"]
                ).strip()
                if soup.head
                else "",
            }
        )
