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

import random
import sys
import traceback
from datetime import datetime
from functools import cache
from typing import Optional
from urllib.parse import quote_plus

from ansi2html import Ansi2HTMLConverter  # type: ignore
from tornado import httputil
from tornado.web import HTTPError, RequestHandler

from an_website.utils.utils import (
    REPO_URL,
    THEMES,
    ModuleInfo,
    add_args_to_url,
    str_to_bool,
)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        "Utilitys",
        "Nütliche Werkzeuge für alle möglichen Sachen.",
        handlers=(
            (r"/error/?", ZeroDivision, {}),
            (r"/([1-5][0-9]{2}).html", ErrorPage, {}),
        ),
    )


class BaseRequestHandler(RequestHandler):
    """The base tornado request handler used by every page."""

    RATELIMIT_TOKENS: int = 1  # can be overridden in subclasses
    REQUIRES_AUTHORIZATION: bool = False  # can be overridden in subclasses

    # info about page, can be overridden in module_info
    title = "Das Asoziale Netzwerk"
    description = "Die tolle Webseite des Asozialen Netzwerkes"
    module_info: ModuleInfo

    def initialize(self, **kwargs):
        """
        Get title and description from the kwargs.

        If title and description are present in the kwargs they
        override self.title and self.description.
        """
        self.module_info: ModuleInfo = kwargs.get("module_info")
        self.title = kwargs.get("title", self.title)
        self.description = kwargs.get("description", self.description)

    def data_received(self, chunk):
        """Do nothing."""

    async def prepare(self):  # pylint: disable=invalid-overridden-method
        """Check authorization and rate limits with redis."""
        if self.REQUIRES_AUTHORIZATION and not self.is_authorized():
            # TODO: self.set_header("WWW-Authenticate")
            raise HTTPError(401)

        if (
            # ignore ratelimits in dev_mode
            not sys.flags.dev_mode
            # ignore ratelimits for authorized requests
            and not self.is_authorized()
            # ignore Delimits for requests with method OPTIONS
            and not self.request.method == "OPTIONS"
        ):
            now = datetime.utcnow()
            redis = self.settings.get("REDIS")
            prefix = self.settings.get("REDIS_PREFIX")
            tokens = getattr(
                self, "RATELIMIT_TOKENS_" + self.request.method, None
            )
            if tokens is None:
                tokens = self.RATELIMIT_TOKENS
            result = await redis.execute_command(
                "CL.THROTTLE",
                prefix + "ratelimit:" + self.request.remote_ip,
                15,  # max burst
                30,  # count per period
                60,  # period
                tokens,
            )
            self.set_header("X-RateLimit-Limit", result[1])
            self.set_header("X-RateLimit-Remaining", result[2])
            self.set_header("Retry-After", result[3])
            self.set_header("X-RateLimit-Reset", result[4])
            if result[0]:
                if now.month == 4 and now.day == 20:
                    self.set_status(420, "Enhance Your Calm")
                    self.write_error(420)
                else:
                    self.set_status(429)
                    self.write_error(429)

    def write_error(self, status_code, **kwargs):
        """Render the error page with the status_code as a html page."""
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
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
            url = (
                f"/redirect?to={quote_plus(url)}&from"
                f"={quote_plus(this_url)}"
            )

        url = add_args_to_url(
            url,
            # the no_2rd_party param:
            no_3rd_party=True
            if "no_3rd_party" in self.request.query_arguments
            and self.get_no_3rd_party()
            else None,
            # the theme param:
            theme=self.get_theme()
            if "theme" in self.request.query_arguments
            and self.get_theme() != "default"
            else None,
        )

        if url.startswith("/"):
            # don't use relative urls
            protocol = (  # make all links https if the config is set
                "https"
                if self.settings.get("LINK_TO_HTTPS")
                else self.request.protocol
            )
            return f"{protocol}://{self.request.host}{url}"

        return url

    @cache
    def get_no_3rd_party(self) -> bool:
        """Return the no_3rd_party query argument as boolean."""
        no_3rd_party = self.get_request_var_as_bool(
            "no_3rd_party", default=False
        )
        return False if no_3rd_party is None else no_3rd_party

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
            and self.get_no_3rd_party()
        ):
            form_appendix = (
                "<input name='no_3rd_party' class='hidden-input' value='sure'>"
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
                "keywords": f"Asoziales Netzwerk, Känguru-Chroniken, "
                f"{self.module_info.get_keywords_as_str()}",
                "no_3rd_party": self.get_no_3rd_party(),
                "lang": "de",  # can change in future
                "form_appendix": self.get_form_appendix(),
                "fix_url": self.fix_url,
                "REPO_URL": self.fix_url(REPO_URL),
                "theme": self.get_display_theme(),
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

    def write_error(self, status_code, **kwargs):
        """Finish with the status code and the reason as dict."""
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    RATELIMIT_TOKENS = 0

    async def prepare(self):
        """Throw a 404 http error."""
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
        )


class ZeroDivision(BaseRequestHandler):
    """A fun request handler that throws an error."""

    RATELIMIT_TOKENS = 10

    async def prepare(self):
        """Divide by zero and throw an error."""
        if not self.request.method == "OPTIONS":
            await super().prepare()
            await self.finish(str(0 / 0))
