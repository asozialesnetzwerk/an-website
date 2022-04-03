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
The base request handlers used by other modules.

This should only contain request handlers and the get_module_info function.
"""

from __future__ import annotations

import inspect
import logging
import os
import random
import re
import sys
import time
import traceback
import uuid
from collections.abc import Awaitable, Coroutine
from datetime import datetime, timedelta
from http.client import responses
from typing import Any, cast
from urllib.parse import SplitResult, quote, unquote, urlsplit, urlunsplit

import elasticapm  # type: ignore
import orjson as json
from ansi2html import Ansi2HTMLConverter  # type: ignore
from blake3 import blake3  # type: ignore
from bs4 import BeautifulSoup
from elasticsearch import AsyncElasticsearch
from Levenshtein import distance  # type: ignore
from redis.asyncio import Redis  # type: ignore
from tornado import web
from tornado.concurrent import Future  # pylint: disable=unused-import
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError, MissingArgumentError, RequestHandler

from .. import DIR as ROOT_DIR
from .. import REPO_URL
from .static_file_handling import fix_static_url
from .utils import (
    THEMES,
    ModuleInfo,
    Permissions,
    add_args_to_url,
    anonymize_ip,
    bool_to_str,
    geoip,
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
            (
                r"/error",
                ZeroDivision if sys.flags.dev_mode else NotFoundHandler,
                {},
            ),
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
    """The base Tornado request handler used by every page and API."""

    REQUIRED_PERMISSION: Permissions = Permissions(0)
    # the following should be False on security relevant endpoints
    SUPPORTS_COOKIE_AUTHORIZATION: bool = True
    ALLOWED_METHODS: tuple[str, ...] = ("GET",)

    ELASTIC_RUM_JS_URL = (
        "/@elastic/apm-rum@^5/dist/bundles/elastic-apm-rum"
        f".umd{'.min' if not sys.flags.dev_mode else ''}.js"
    )

    module_info: ModuleInfo
    # info about page, can be overridden in module_info
    title = "Das Asoziale Netzwerk"
    short_title = "Asoziales Netzwerk"
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
        # see: dev.mozilla.org/docs/Web/HTTP/Headers
        # Opt out of all FLoC cohort calculation.
        self.set_header("Permissions-Policy", "interest-cohort=()")
        # send only origin in Referer header if request is cross-origin
        self.set_header("Referrer-Policy", "origin-when-cross-origin")
        if self.settings.get("HSTS"):
            # dev.mozilla.org/docs/Web/HTTP/Headers/Strict-Transport-Security
            self.set_header(
                "Strict-Transport-Security", "max-age=31536000; preload"
            )
        if (
            _oa := self.settings.get("ONION_ADDRESS")
        ) and not self.request.host_name.endswith(".onion"):
            # community.torproject.org/onion-services/advanced/onion-location
            self.set_header(
                "Onion-Location",
                _oa
                + self.request.path
                + (f"?{self.request.query}" if self.request.query else ""),
            )
        if self.settings.get("debug"):
            self.set_header("X-Dev-Mode", bool_to_str(True))
            for permission in Permissions:
                if permission.name:
                    self.set_header(
                        f"X-Permission-{permission.name}",
                        bool_to_str(self.is_authorized(permission)),
                    )

    async def prepare(  # pylint: disable=invalid-overridden-method
        self,
    ) -> None:
        """Check authorization and call self.ratelimit()."""
        if self.request.method == "GET":

            if self.redirect_to_canonical_domain():
                return

            if (days := random.randint(0, 31337)) in {69, 420, 1337, 31337}:
                self.set_cookie("c", "s", expires_days=days / 24, path="/")

        if self.request.method != "OPTIONS":

            if not self.is_authorized(self.REQUIRED_PERMISSION):
                # TODO: self.set_header("WWW-Authenticate")
                logger.info(
                    "Unauthorized access to %s from %s",
                    self.request.path,
                    anonymize_ip(str(self.request.remote_ip)),
                )
                raise HTTPError(401)

            if not await self.ratelimit(True):
                await self.ratelimit()

    def redirect_to_canonical_domain(self) -> bool:
        """Redirect to the canonical domain."""
        if (
            not (domain := self.settings.get("DOMAIN"))
            or not self.request.headers.get("Host")
            or self.request.host_name == domain
            or self.request.host_name.endswith((".onion", ".i2p"))
            or re.fullmatch(r"/[\u2800-\u28FF]+/?", self.request.path)
        ):
            return False
        port = urlsplit(f"//{self.request.headers['Host']}").port
        self.redirect(
            urlsplit(self.request.full_url())
            ._replace(netloc=f"{domain}:{port}" if port else domain)
            .geturl(),
            permanent=True,
        )
        return True

    async def ratelimit(self, global_ratelimit: bool = False) -> bool:
        """Take b1nzy to space using Redis."""
        # pylint: disable=too-complex
        if (
            not self.settings.get("RATELIMITS")
            or self.request.method == "OPTIONS"
            or self.is_authorized(Permissions.RATELIMITS)
        ):
            return False
        remote_ip = blake3(
            cast(str, self.request.remote_ip).encode("ascii")
        ).hexdigest()
        method = self.request.method
        if method == "HEAD":
            method = "GET"
        if global_ratelimit:
            key = f"{self.redis_prefix}:ratelimit:{remote_ip}"
            max_burst = 99  # limit = 100
            count_per_period = 20  # 20 requests per 1 second
            period = 1
            tokens = 10 if self.settings.get("UNDER_ATTACK") else 1
        else:
            bucket = getattr(
                self,
                f"RATELIMIT_{method}_BUCKET",
                self.__class__.__name__.lower(),
            )
            limit = getattr(self, f"RATELIMIT_{method}_LIMIT", 0)
            if not limit:
                return False
            key = f"{self.redis_prefix}:ratelimit:{remote_ip}:{bucket}"
            max_burst = limit - 1
            count_per_period = getattr(  # request count per period
                self,
                f"RATELIMIT_{method}_COUNT_PER_PERIOD",
                30,
            )
            period = getattr(
                self, f"RATELIMIT_{method}_PERIOD", 60  # period in seconds
            )
            tokens = 1 if self.request.method != "HEAD" else 0
        if self.redis is None:
            raise HTTPError(
                503,
                "Ratelimits are enabled, but Redis is not available. "
                "This can happen shortly after starting the website.",
            )
        result = await self.redis.execute_command(
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
            self.set_header("X-RateLimit-Limit", str(result[1]))
            self.set_header("X-RateLimit-Remaining", str(result[2]))
            self.set_header("X-RateLimit-Reset", str(time.time() + reset_after))
            self.set_header("X-RateLimit-Reset-After", str(reset_after))
            self.set_header(
                "X-RateLimit-Bucket",
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

    @classmethod
    def supports_head(cls) -> bool:
        """Check whether this request handler supports HEAD requests."""
        signature = inspect.signature(cls.get)
        return (
            "head" in signature.parameters
            and signature.parameters["head"].kind
            == inspect.Parameter.KEYWORD_ONLY
        )

    @classmethod
    def get_allowed_methods(cls) -> list[str]:
        """Get allowed methods."""
        methods = ["OPTIONS"]
        if "GET" in cls.ALLOWED_METHODS and cls.supports_head():
            methods.append("HEAD")
        methods.extend(cls.ALLOWED_METHODS)
        return methods

    def options(self, *args: Any, **kwargs: Any) -> None:
        """Handle OPTIONS requests."""
        # pylint: disable=unused-argument
        self.set_header("Allow", ", ".join(self.get_allowed_methods()))
        self.set_status(204)
        self.finish()

    def head(self, *args: Any, **kwargs: Any) -> None | Awaitable[None]:
        """Handle HEAD requests."""
        if self.get.__module__ == "tornado.web":
            raise HTTPError(405)
        if not self.supports_head():
            raise HTTPError(501)
        kwargs["head"] = True
        return self.get(*args, **kwargs)

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

    def get_error_message(self, **kwargs: Any) -> str:
        """
        Get the error message and return it.

        If the serve_traceback setting is true (debug mode is activated),
        the traceback gets returned.
        """
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            if self.settings.get("serve_traceback") or self.is_authorized(
                Permissions.TRACEBACK
            ):
                return "".join(
                    traceback.format_exception(*kwargs["exc_info"])
                ).strip()
            return "".join(
                traceback.format_exception_only(*kwargs["exc_info"][:2])
            ).strip()
        if "exc_info" in kwargs and issubclass(
            kwargs["exc_info"][0], MissingArgumentError
        ):
            return cast(str, kwargs["exc_info"][1].log_message)
        return str(self._reason)

    def get_user_id(self) -> str:
        """Get the user id saved in the cookie or create one."""
        _user_id = self.get_secure_cookie(
            "user_id",
            max_age_days=90,
            min_version=2,
        )
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

    def get_module_infos(self) -> tuple[ModuleInfo, ...]:
        """Get the module infos."""
        return self.settings.get("MODULE_INFOS") or tuple()

    def fix_url(  # pylint: disable=too-complex
        self,
        url: None | str | SplitResult = None,
        this_url: None | str = None,
        always_add_params: bool = False,
        new_path: None | str = None,
        **query_args: None | str | bool | float,
    ) -> str:
        """
        Fix a URL and return it.

        If the URL is from another website, link to it with the redirect page.
        Otherwise just return the URL with no_3rd_party appended.
        """
        if url is None:
            url = self.request.full_url()

        if isinstance(url, str):
            url = urlsplit(url)

        if url.netloc and url.netloc.lower() != self.request.host.lower():
            # URL is to other website:
            url = urlsplit(
                f"/redirect?to={quote(url.geturl())}"
                f"&from={quote(this_url or self.request.full_url())}"
            )

        if "no_3rd_party" not in query_args:
            query_args["no_3rd_party"] = self.get_no_3rd_party()
        if "theme" not in query_args:
            query_args["theme"] = self.get_theme()
        if "dynload" not in query_args:
            query_args["dynload"] = self.get_dynload()

        # don't add as_json=nope to url if as_json is False
        # pylint: disable=compare-to-zero  # if None it shouldn't be deleted
        if "as_json" in query_args and query_args["as_json"] is False:
            del query_args["as_json"]

        if not always_add_params:
            if query_args["no_3rd_party"] == self.get_saved_no_3rd_party():
                query_args["no_3rd_party"] = None
            if query_args["theme"] == self.get_saved_theme():
                query_args["theme"] = None
            if query_args["dynload"] == self.get_saved_dynload():
                query_args["dynload"] = None

        return add_args_to_url(
            urlunsplit(
                (
                    self.request.protocol,
                    self.request.host,
                    (new_path or url.path).rstrip("/"),
                    url.query,
                    url.fragment,
                )
            ),
            **query_args,
        )

    def get_as_json(self) -> bool:
        """Get the value of the as_json query parameter."""
        return str_to_bool(
            self.get_query_argument("as_json", default="nope"), False
        )

    def get_no_3rd_party_default(self) -> bool:
        """Get the default value for the no_3rd_party param."""
        return self.request.host_name.endswith((".onion", ".i2p"))

    def get_saved_no_3rd_party(self) -> bool:
        """Get the saved value for no_3rd_party."""
        default = self.get_no_3rd_party_default()
        no_3rd_party = self.get_cookie("no_3rd_party")
        if no_3rd_party is None:
            return default
        return str_to_bool(no_3rd_party, default)

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

    def get_theme(self) -> str:
        """Get the theme currently selected."""
        theme = self.get_argument("theme", default=None)
        if theme in THEMES:
            return theme
        return self.get_saved_theme()

    def get_display_theme(self) -> str:
        """Get the theme currently displayed."""
        if "random" not in (theme := self.get_theme()):
            return theme

        # theme names to ignore:
        ignore_themes = ["random", "random-dark"]

        if theme == "random-dark":
            ignore_themes.extend(("light", "light-blue", "fun"))

        return random.choice(
            tuple(theme for theme in THEMES if theme not in ignore_themes)
        )

    def get_contact_address(self) -> None | str:
        """Get the contact address from the settings."""
        address: None | str = self.settings.get("CONTACT_ADDRESS")
        if not address:
            return None
        if not address.startswith("@"):
            return address
        # if address starts with @ it's a catch-all address
        return name_to_id(self.request.path) + "_contact" + address

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
        except Exception:  # pylint: disable=broad-except
            pass
        else:
            if isinstance(body, dict) and name in body:
                val = str(body[name])
                return val.strip() if strip else val

        # pylint: disable=protected-access
        if isinstance(default, web._ArgDefaultMarker):
            raise web.MissingArgumentError(name)

        return default

    def is_authorized(self, permission: Permissions) -> bool:
        """Check whether the request is authorized."""
        if permission == Permissions(0):
            return True
        api_secrets = self.settings.get("TRUSTED_API_SECRETS", {})
        return any(
            permission in api_secrets[key]
            for key in (
                self.request.headers.get("Authorization"),
                self.get_argument("key", default=None),
                self.get_cookie("key", default=None)
                if self.SUPPORTS_COOKIE_AUTHORIZATION
                else None,
            )
            if key is not None and key in api_secrets
        )

    def geoip(
        self,
        ip: None | str = None,  # pylint: disable=invalid-name
        database: str = geoip.__defaults__[0],  # type: ignore
    ) -> Coroutine[Any, Any, None | dict[str, Any]]:
        """Get GeoIP information."""
        if not ip:
            ip = str(self.request.remote_ip)
        return geoip(ip, database, self.elasticsearch)


class HTMLRequestHandler(BaseRequestHandler):
    """A request handler that serves HTML files."""

    used_render = False

    def get_form_appendix(self) -> str:
        """Get HTML to add to forms to keep important query args."""
        form_appendix: str

        form_appendix = (
            "<input name='no_3rd_party' class='hidden-input' "
            f"value='{bool_to_str(self.get_no_3rd_party())}'>"
            if "no_3rd_party" in self.request.query_arguments
            and self.get_no_3rd_party() != self.get_saved_no_3rd_party()
            else ""
        )

        if self.get_dynload() != self.get_saved_dynload():
            form_appendix += (
                "<input name='dynload' class='hidden-input' "
                f"value='{bool_to_str(self.get_dynload())}'>"
            )

        if (theme := self.get_theme()) != self.get_saved_theme():
            form_appendix += (
                f"<input name='theme' class='hidden-input' value='{theme}'>"
            )

        return form_appendix

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Render the error page with the status_code as a HTML page."""
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
            description=self.get_error_page_description(status_code),
            is_traceback="exc_info" in kwargs
            and not issubclass(kwargs["exc_info"][0], HTTPError)
            and (
                self.settings.get("serve_traceback")
                or self.is_authorized(Permissions.TRACEBACK)
            ),
        )

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
                "lang": "de",  # TODO: add language support
                "form_appendix": self.get_form_appendix(),
                "fix_url": self.fix_url,
                "fix_static": lambda url: self.fix_url(fix_static_url(url)),
                "REPO_URL": self.fix_url(REPO_URL),
                "theme": self.get_display_theme(),
                "contact_address": self.get_contact_address(),
                "elastic_rum_js_url": self.ELASTIC_RUM_JS_URL,
                "canonical_url": self.fix_url(
                    self.request.full_url().upper()
                    if self.request.path.upper().startswith("/LOLWUT")
                    else self.request.full_url().lower()
                ).split("?")[0],
                "settings": self.settings,
                "c": str_to_bool(self.get_cookie("c", "n"), False)
                or (now := datetime.utcnow()).day == 1
                and now.month == 4,
                "dynload": self.get_dynload(),
                "as_json": self.get_as_json(),
            }
        )
        return namespace

    def render(self, template_name: str, **kwargs: Any) -> "Future[None]":
        """Render a template."""
        self.used_render = True
        return super().render(template_name, **kwargs)

    def finish(
        self, chunk: None | str | bytes | dict[Any, Any] = None
    ) -> "Future[None]":
        """Finish the request."""
        if (
            isinstance(chunk, dict)
            or chunk is None
            or not self.used_render
            or getattr(self, "IS_NOT_HTML", False)
            or not self.get_as_json()
        ):
            return super().finish(chunk)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Allow-Methods", "OPTIONS, HEAD, GET")
        soup = BeautifulSoup(
            chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk,
            features="lxml",
        )
        return super().finish(
            {
                "url": self.fix_url(  # request url without as_json param
                    self.request.full_url(), as_json=None
                ),
                "title": self.title,
                "short_title": self.short_title
                if self.title != self.short_title
                else None,
                "body": "".join(
                    str(_el)
                    for _el in soup.find_all(name="main", id="body")[0].contents
                ).strip(),
                "scripts": [
                    {
                        "src": _s.get("src"),
                        "script": _s.string,
                        "onload": _s.get("onload"),
                    }
                    for _s in soup.find_all("script")
                    # if "on-every-page" not in _s.attrs # (curr not used)
                ]
                if soup.head
                else [],
                "stylesheets": (
                    [
                        str(_s.get("href")).strip()
                        for _s in soup.find_all("link", rel="stylesheet")
                        # if "on-every-page" not in _s.attrs # (curr not used)
                    ]
                )
                if soup.head
                else [],
                "css": "\n".join(
                    str(_s.string or "")
                    for _s in soup.find_all("style")
                    # if "on-every-page" not in _s.attrs # (curr not used)
                ).strip()
                if soup.head
                else "",
            }
        )


class APIRequestHandler(BaseRequestHandler):
    """
    The base API request handler.

    It overrides the write error method to return errors as JSON.
    """

    def set_default_headers(self) -> None:
        """Set important default headers for the API request handlers."""
        super().set_default_headers()
        # see header docs at: dev.mozilla.org/docs/Web/HTTP/Headers
        self.set_header("Access-Control-Max-Age", "7200")
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header(
            "Access-Control-Allow-Methods",
            ", ".join(self.get_allowed_methods()),
        )

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Finish with the status code and the reason as dict."""
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )


class NotFoundHandler(HTMLRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing to have default title and desc."""
        if "module_info" not in kwargs:
            kwargs["module_info"] = None
        super().initialize(*args, **kwargs)

    async def prepare(self) -> None:
        """Throw a 404 HTTP error or redirect to another page."""
        if self.request.method not in ("GET", "HEAD"):
            raise HTTPError(404)

        new_path = (
            re.sub(r"/+", "/", self.request.path.rstrip("/"))
            .replace("_", "-")
            .removesuffix("/index.html")
            .removesuffix("/index.htm")
            .removesuffix("/index.php")
            .removesuffix(".html")
            .removesuffix(".htm")
            .removesuffix(".php")
        )

        if new_path.lower() in {
            "/-profiler/phpinfo",
            "/.aws/credentials",
            "/.env",
            "/.env.bak",
            "/.ftpconfig",
            "/admin/controller/extension/extension",
            "/assets/filemanager/dialog",
            "/assets/vendor/server/php",
            "/aws.yml",
            "/boaform/admin/formlogin",
            "/phpinfo",
            "/public/assets/jquery-file-upload/server/php",
            "/root",
            "/settings/aws.yml",
            "/uploads",
            "/vendor/phpunit/phpunit/src/util/php/eval-stdin",
            "/wordpress",
            "/wp",
            "/wp-admin",
            "/wp-admin/css",
            "/wp-includes",
            "/wp-login",
            "/wp-upload",
        }:
            raise HTTPError(469, reason="Nice Try")

        if new_path != self.request.path:
            return self.redirect(self.fix_url(new_path=new_path), True)

        this_path_stripped = unquote(new_path).strip("/")  # "/%20/" → " "
        distances: list[tuple[int, str]] = []
        max_dist = max(1, min(4, len(this_path_stripped) - 1))

        for module_info in self.get_module_infos():
            if module_info.path is not None:
                dist = min(  # get the smallest distance with the aliases
                    distance(this_path_stripped, path.strip("/"))
                    for path in (*module_info.aliases, module_info.path)
                    if path != "/z"  # do not redirect to /z
                )
                if dist <= max_dist:
                    # only if the distance is less than or equal {max_dist}
                    distances.append((dist, module_info.path))
            if len(module_info.sub_pages) > 0:
                distances.extend(
                    (
                        distance(this_path_stripped, sub_page.path.strip("/")),
                        sub_page.path,
                    )
                    for sub_page in module_info.sub_pages
                    if sub_page.path is not None
                )

        if len(distances) > 0:
            # sort to get the one with the smallest distance in index 0
            distances.sort()
            dist, path = distances[0]
            # redirect only if the distance is less than or equal {max_dist}
            if dist <= max_dist:
                return self.redirect(self.fix_url(new_path=path), False)

        raise HTTPError(404)


class ErrorPage(HTMLRequestHandler):
    """A request handler that shows the error page."""

    async def get(self, code: str) -> None:
        """Show the error page."""
        status_code: int = int(code)
        # get the reason
        reason: str = responses.get(status_code, "")
        # set the status code if Tornado doesn't raise an error if it is set
        if status_code not in (204, 304) and not 100 <= status_code < 200:
            self.set_status(status_code)  # set the status code
        return await self.render(
            "error.html",
            status=status_code,
            reason=reason,
            description=self.get_error_page_description(status_code),
            is_traceback=False,
        )


class ZeroDivision(HTMLRequestHandler):
    """A request handler that raises an error."""

    async def prepare(self) -> None:
        """Divide by zero and raise an error."""
        if not self.request.method == "OPTIONS":
            420 / 0  # pylint: disable=pointless-statement


class ElasticRUM(BaseRequestHandler):
    """A request handler that serves the RUM script."""

    URL = (
        "https://unpkg.com/@elastic/apm-rum@{}"
        "/dist/bundles/elastic-apm-rum.umd{}.js{}"
    )
    SCRIPTS: dict[str, tuple[str, float]] = {}
    CACHE_TIME = 365 * 60 * 60 * 24

    async def get(self, version: str, spam: str = "", eggs: str = "") -> None:
        """Serve the RUM script."""
        key = version + spam + eggs
        if key not in self.SCRIPTS or self.SCRIPTS[key][1] < time.monotonic():
            response = await AsyncHTTPClient().fetch(
                self.URL.format(version, spam, eggs),
                raise_error=False,
                ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
            )
            if response.code != 200:
                raise HTTPError(response.code, reason=response.reason)
            self.SCRIPTS[key] = (
                response.body.decode(),
                time.monotonic() + 365 * 60 * 60 * 24,
            )
            new_path = urlsplit(response.effective_url).path
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
            "Expires", datetime.utcnow() + timedelta(seconds=self.CACHE_TIME)
        )
        self.set_header(
            "Cache-Control", f"public, min-fresh={self.CACHE_TIME}, immutable"
        )
        return await self.finish(self.SCRIPTS[key][0])
