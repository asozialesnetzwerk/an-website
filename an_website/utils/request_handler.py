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
import random
import re
import sys
import time
import traceback
import uuid
from asyncio import Future
from base64 import b64decode
from collections.abc import Awaitable, Coroutine
from datetime import date, datetime, timedelta, timezone, tzinfo
from http.client import responses
from typing import Any, cast
from urllib.parse import SplitResult, quote, unquote, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import elasticapm  # type: ignore
import orjson as json
from ansi2html import Ansi2HTMLConverter  # type: ignore
from blake3 import blake3  # type: ignore
from bs4 import BeautifulSoup
from dateutil.easter import easter
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ElasticsearchException
from Levenshtein import distance  # type: ignore
from redis.asyncio import Redis
from sympy.ntheory import isprime
from tornado.web import HTTPError, MissingArgumentError, RequestHandler

from .. import EVENT_ELASTICSEARCH, EVENT_REDIS, REPO_URL
from .static_file_handling import fix_static_url
from .utils import (
    THEMES,
    ModuleInfo,
    Permissions,
    add_args_to_url,
    anonymize_ip,
    bool_to_str,
    geoip,
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

    _active_origin_trials: set[str]

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
    def redis(self) -> Redis:  # type: ignore[type-arg]
        """Get the Redis client from the settings."""
        return cast(Redis, self.settings.get("REDIS"))  # type: ignore[type-arg]

    @property
    def redis_prefix(self) -> str:
        """Get the Redis prefix from the settings."""
        return self.settings.get("REDIS_PREFIX", "")

    @property
    def elasticsearch(self) -> AsyncElasticsearch:
        """Get the Elasticsearch client from the settings."""
        return cast(AsyncElasticsearch, self.settings.get("ELASTICSEARCH"))

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
        self._active_origin_trials = set()
        # dev.mozilla.org/docs/Web/HTTP/Headers
        self.set_header("Access-Control-Max-Age", "7200")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header(
            "Access-Control-Allow-Methods",
            ", ".join(self.get_allowed_methods()),
        )
        # Opt out of all FLoC cohort calculation.
        self.set_header("Permissions-Policy", "interest-cohort=()")
        # don't send the Referer header for cross-origin requests
        self.set_header("Referrer-Policy", "same-origin")
        # dev.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/SharedArrayBuffer
        self.set_header("Cross-Origin-Opener-Policy", "same-origin")
        if self.request.path != "/kaenguru-comics":  # TODO: make this better
            self.set_header("Cross-Origin-Embedder-Policy", "require-corp")
        if self.settings.get("HSTS"):
            # dev.mozilla.org/docs/Web/HTTP/Headers/Strict-Transport-Security
            self.set_header("Strict-Transport-Security", "max-age=63072000")
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
            self.set_header("X-Debug", bool_to_str(True))
            for permission in Permissions:
                if permission.name:
                    self.set_header(
                        f"X-Permission-{permission.name}",
                        bool_to_str(self.is_authorized(permission)),
                    )
        self.origin_trial(
            "AjM7i7vhQFI2RUcab3ZCsJ9RESLDD9asdj0MxpwxHXXtETlsm8dEn+HSd646oPr1dKjn+EcNEj8uV3qFGJzObgsAAAB3eyJvcmlnaW4iOiJodHRwczovL2Fzb3ppYWwub3JnOjQ0MyIsImZlYXR1cmUiOiJTZW5kRnVsbFVzZXJBZ2VudEFmdGVyUmVkdWN0aW9uIiwiZXhwaXJ5IjoxNjg0ODg2Mzk5LCJpc1N1YmRvbWFpbiI6dHJ1ZX0="  # noqa: B950  # pylint: disable=line-too-long, useless-suppression
        )

    def origin_trial(self, token: str | bytes) -> bool:
        """Enable an experimental feature."""
        # pylint: disable=protected-access
        if token in self._active_origin_trials:
            return True
        url = urlsplit(self.request.full_url())
        payload = json.loads(b64decode(token)[69:])
        origin = urlsplit(payload["origin"])
        if url.port is None and url.scheme in {"http", "https"}:
            url = url._replace(
                netloc=f"{url.hostname}:{443 if url.scheme == 'https' else 80}"
            )
        if self.request._start_time > payload["expiry"]:
            return False
        if url.scheme != origin.scheme:
            return False
        if url.netloc != origin.netloc and not (
            payload.get("isSubdomain")
            and url.netloc.endswith(f".{origin.netloc}")
        ):
            return False
        self.add_header("Origin-Trial", token)
        self._active_origin_trials.add(
            token if isinstance(token, str) else token.decode("ascii")
        )
        return True

    def set_cookie(  # pylint: disable=too-many-arguments
        self,
        name: str,
        value: str | bytes,
        domain: None | str = None,
        expires: None | float | tuple[int, ...] | datetime = None,
        path: str = "/",
        expires_days: None | float = 365,  # changed
        **kwargs: Any,
    ) -> None:
        """Override the set_cookie method to set expires days."""
        if "samesite" not in kwargs:
            # default for same site should be strict
            kwargs["samesite"] = "Strict"

        super().set_cookie(
            name,
            value,
            domain,
            expires,
            path,
            expires_days,
            **kwargs,
        )

    async def prepare(  # pylint: disable=invalid-overridden-method
        self,
    ) -> None:
        """Check authorization and call self.ratelimit()."""
        # pylint: disable=attribute-defined-outside-init
        self.now = await self.get_time()

        if self.request.method == "GET":

            if self.redirect_to_canonical_domain():
                return

            if not self.settings.get("TESTING"):
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
                raise HTTPError(403)

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
        if not EVENT_REDIS.is_set():
            raise HTTPError(
                503,
                "Ratelimits are enabled, but Redis is not available. "
                "This can happen shortly after starting the website.",
            )
        result = await self.redis.execute_command(  # type: ignore[no-untyped-call]
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
            if self.now.date() == date(self.now.year, 4, 20):
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
        if not self.get_secure_cookie(
            "user_id", max_age_days=30, min_version=2
        ):
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

    def fix_url(  # noqa: C901
        self,
        url: None | str | SplitResult = None,
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
            url = urlsplit(f"/redirect?to={quote(url.geturl())}")
        path = url.path if new_path is None else new_path  # the path of the url
        # don't add as_json=nope to url if as_json is False
        # pylint: disable=compare-to-zero  # if None it shouldn't be deleted
        if "as_json" in query_args and query_args["as_json"] is False:
            del query_args["as_json"]
        if path.startswith(("/static/", "/soundboard/files/")):
            query_args.update(no_3rd_party=None, theme=None, dynload=None)
        else:
            query_args.setdefault("no_3rd_party", self.get_no_3rd_party())
            query_args.setdefault("theme", self.get_theme())
            query_args.setdefault("dynload", self.get_dynload())
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
                    path.rstrip("/"),
                    url.query,
                    url.fragment,
                )
            ),
            **query_args,
        )

    def get_as_json(self) -> bool:
        """Get the value of the as_json query parameter."""
        return self.get_bool_argument("as_json", default=False)

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
        return self.get_bool_argument(
            "no_3rd_party", default=self.get_saved_no_3rd_party()
        )

    def get_saved_dynload(self) -> bool:
        """Get the saved value for dynload."""
        default = False  # TODO: change this
        dynload = self.get_cookie("dynload")
        if dynload is None:
            return default
        return str_to_bool(dynload, default)

    def get_dynload(self) -> bool:
        """Return the dynload query argument as boolean."""
        return self.get_bool_argument("dynload", self.get_saved_dynload())

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

        ignore_themes = ["random", "random-dark"]

        if theme == "random-dark":
            ignore_themes.extend(("light", "light-blue", "fun"))

        return random.choice(
            tuple(theme for theme in THEMES if theme not in ignore_themes)
        )

    def get_bool_argument(
        self,
        name: str,
        default: None | bool = None,
    ) -> bool:
        """Get an argument parsed as boolean."""
        if default is not None:
            return str_to_bool(
                self.get_argument(name, bool_to_str(default)) or "", default
            )
        value = str(self.get_argument(name))
        try:
            return str_to_bool(value)
        except ValueError as err:
            raise HTTPError(400, f"{value} is not a Boolean.") from err

    def is_authorized(self, permission: Permissions) -> bool:
        """Check whether the request is authorized."""
        found_keys: list[None | str] = []
        if permission == Permissions(0):
            return True
        api_secrets = self.settings.get("TRUSTED_API_SECRETS", {})
        found_keys.extend(self.request.headers.get_list("Authorization"))
        found_keys.extend(self.get_arguments("key"))
        if self.SUPPORTS_COOKIE_AUTHORIZATION:
            found_keys.append(self.get_cookie("key", default=None))
        return any(
            permission in api_secrets[key]
            for key in found_keys
            if key and key in api_secrets
        )

    def geoip(
        self,
        ip: None | str = None,  # pylint: disable=invalid-name
        database: str = geoip.__defaults__[0],  # type: ignore
    ) -> Coroutine[Any, Any, None | dict[str, Any]]:
        """Get GeoIP information."""
        if not ip:
            ip = str(self.request.remote_ip)
        if not EVENT_ELASTICSEARCH.is_set():
            return geoip(ip, database)
        return geoip(ip, database, self.elasticsearch)

    async def get_time(self) -> datetime:
        """Get the start time of the request in the user's timezone."""
        tz: tzinfo = timezone.utc  # pylint: disable=invalid-name
        try:
            geoip = await self.geoip()  # pylint: disable=redefined-outer-name
        except ElasticsearchException as exc:
            logger.exception(exc)
            apm: None | elasticapm.Client = self.settings.get(
                "ELASTIC_APM_CLIENT"
            )
            if apm:
                apm.capture_exception()
        else:
            if geoip and "timezone" in geoip:
                tz = ZoneInfo(geoip["timezone"])  # pylint: disable=invalid-name
        return datetime.fromtimestamp(
            self.request._start_time, tz=tz  # pylint: disable=protected-access
        )


class HTMLRequestHandler(BaseRequestHandler):
    """A request handler that serves HTML."""

    used_render = False

    def get_form_appendix(self) -> str:
        """Get HTML to add to forms to keep important query args."""
        form_appendix = (
            "<input name='no_3rd_party' class='hidden' "
            f"value='{bool_to_str(self.get_no_3rd_party())}'>"
            if "no_3rd_party" in self.request.query_arguments
            and self.get_no_3rd_party() != self.get_saved_no_3rd_party()
            else ""
        )
        if self.get_dynload() != self.get_saved_dynload():
            form_appendix += (
                "<input name='dynload' class='hidden' "
                f"value='{bool_to_str(self.get_dynload())}'>"
            )
        if (theme := self.get_theme()) != self.get_saved_theme():
            form_appendix += (
                f"<input name='theme' class='hidden' value='{theme}'>"
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
            ansi2html=Ansi2HTMLConverter(inline=True, scheme="xterm"),
            title=self.title,
            short_title=self.short_title,
            description=self.description,
            keywords="Asoziales Netzwerk, Känguru-Chroniken"
            + (
                f", {self.module_info.get_keywords_as_str(self.request.path)}"
                if self.module_info
                else ""
            ),
            no_3rd_party=self.get_no_3rd_party(),
            lang="de",  # TODO: add language support
            form_appendix=self.get_form_appendix(),
            fix_url=self.fix_url,
            fix_static=lambda url: self.fix_url(fix_static_url(url)),
            REPO_URL=REPO_URL,
            theme=self.get_display_theme(),
            elastic_rum_js_url=self.ELASTIC_RUM_JS_URL,
            canonical_url=self.fix_url(
                self.request.full_url().upper()
                if self.request.path.upper().startswith("/LOLWUT")
                else self.request.full_url().lower()
            ).split("?")[0],
            settings=self.settings,
            c=self.settings.get("TESTING")
            or self.now.date() == date(self.now.year, 4, 1)
            or str_to_bool(self.get_cookie("c", "f") or "f", False),
            dynload=self.get_dynload(),
            as_json=self.get_as_json(),
            now=self.now,
        )
        namespace.update(
            {
                "🥚": self.settings.get("TESTING")
                or timedelta()
                <= self.now.date() - easter(self.now.year)
                < timedelta(days=2),
                "🦘": self.settings.get("TESTING")
                or isprime(self.now.microsecond),  # type: ignore[no-untyped-call]
            }
        )
        return namespace

    def render(self, template_name: str, **kwargs: Any) -> Future[None]:
        """Render a template."""
        self.used_render = True
        return super().render(template_name, **kwargs)

    def finish(
        self, chunk: None | str | bytes | dict[Any, Any] = None
    ) -> Future[None]:
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
        soup = BeautifulSoup(
            chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk,
            features="lxml",
        )
        dictionary: dict[str, Any] = dict(
            url=self.fix_url(as_json=None),  # request url without as_json param
            title=self.title,
            short_title=self.short_title
            if self.title != self.short_title
            else None,
            body="".join(
                str(_el)
                for _el in soup.find_all(name="main", id="body")[0].contents
            ).strip(),
            scripts=[
                {
                    "src": _s.get("src"),
                    "script": _s.string,
                    "onload": _s.get("onload"),
                }
                for _s in soup.find_all("script")
            ]
            if soup.head
            else [],
            stylesheets=[
                str(_s.get("href")).strip()
                for _s in soup.find_all("link", rel="stylesheet")
            ]
            if soup.head
            else [],
            css="\n".join(str(_s.string or "") for _s in soup.find_all("style"))
            if soup.head
            else "",
        )
        return super().finish(dictionary)


class APIRequestHandler(BaseRequestHandler):
    """
    The base API request handler.

    It overrides the write error method to return errors as JSON.
    """

    IS_NOT_HTML = True

    def set_default_headers(self) -> None:
        """Set important default headers for the API request handlers."""
        super().set_default_headers()
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def finish_dict(self, **kwargs: Any) -> Future[None]:
        """Finish the request with a JSON response."""
        return self.finish(kwargs)

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Finish with the status code and the reason as dict."""
        self.finish_dict(
            status=status_code,
            reason=self.get_error_message(**kwargs),
        )


class NotFoundHandler(HTMLRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing to have default title and description."""
        if "module_info" not in kwargs:
            kwargs["module_info"] = None
        super().initialize(*args, **kwargs)

    async def prepare(self) -> None:
        """Throw a 404 HTTP error or redirect to another page."""
        # pylint: disable=attribute-defined-outside-init
        self.now = await self.get_time()  # used by get_template_namespace

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
        reason: str = responses.get(status_code, "")  # get the reason
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
