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
The base request handler used by other modules.

This should only contain the BaseRequestHandler class.
"""

from __future__ import annotations

import contextlib
import inspect
import logging
import random
import sys
import traceback
import uuid
from asyncio import Future
from base64 import b64decode
from collections.abc import Awaitable, Callable, Coroutine
from datetime import date, datetime, timezone, tzinfo
from typing import Any, ClassVar, Final, cast
from urllib.parse import SplitResult, quote, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import elasticapm  # type: ignore[import]
import orjson as json
import regex
import yaml
from accept_types import get_best_match  # type: ignore[import]
from elastic_enterprise_search import AppSearch  # type: ignore[import]
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ElasticsearchException
from redis.asyncio import Redis
from tornado.web import (
    GZipContentEncoding,
    HTTPError,
    MissingArgumentError,
    RequestHandler,
)

from .. import (
    EVENT_ELASTICSEARCH,
    EVENT_REDIS,
    NAME,
    ORJSON_OPTIONS,
    pytest_is_running,
)
from .static_file_handling import FILE_HASHES_DICT
from .token import InvalidTokenError, parse_token
from .utils import (
    THEMES,
    BumpscosityValue,
    ModuleInfo,
    OpenMojiValue,
    Permission,
    add_args_to_url,
    anonymize_ip,
    bool_to_str,
    geoip,
    hash_bytes,
    parse_bumpscosity,
    parse_openmoji_arg,
    ratelimit,
    str_to_bool,
)

LOGGER: Final = logging.getLogger(__name__)

TEXT_CONTENT_TYPES: Final[set[str]] = {
    "application/javascript",
    "application/json",
    "application/vnd.asozial.dynload+json",
    "application/x-ndjson",
    "application/xml",
    "application/yaml",
}


class BaseRequestHandler(RequestHandler):
    """The base request handler used by every page and API."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    ELASTIC_RUM_URL: ClassVar[str] = (
        "/@elastic/apm-rum@^5/dist/bundles/elastic-apm-rum"
        f".umd{'.min' if not sys.flags.dev_mode else ''}.js"
    )

    COMPUTE_ETAG: ClassVar[bool] = True
    ALLOW_COMPRESSION: ClassVar[bool] = True
    MAX_BODY_SIZE: ClassVar[None | int] = None
    ALLOWED_METHODS: ClassVar[tuple[str, ...]] = ("GET",)
    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = ()
    REQUIRED_PERMISSION: ClassVar[None | Permission] = None
    # the following should be False on security relevant endpoints
    ALLOW_COOKIE_AUTHENTICATION: ClassVar[bool] = True

    module_info: ModuleInfo
    # info about page, can be overridden in module_info
    title: str = "Das Asoziale Netzwerk"
    short_title: str = "Asoziales Netzwerk"
    description: str = "Die tolle Webseite des Asozialen Netzwerks"

    active_origin_trials: set[bytes]
    content_type: None | str = None
    auth_failed: bool = False
    apm_script: None | str
    crawler: bool = False
    now: datetime

    @property
    def apm_client(self) -> None | elasticapm.Client:
        """Get the APM client from the settings."""
        return self.settings.get("ELASTIC_APM", {}).get("CLIENT")

    @property
    def apm_enabled(self) -> bool:
        """Return whether APM is enabled."""
        return bool(self.settings.get("ELASTIC_APM", {}).get("ENABLED"))

    @property
    def app_search(self) -> None | AppSearch:
        """Get the App Search client from the settings."""
        return self.settings.get("APP_SEARCH")

    @property
    def app_search_engine(self) -> str:
        """Get the App Search engine from the settings."""
        return self.settings.get("APP_SEARCH_ENGINE", NAME.removesuffix("-dev"))

    def compute_etag(self) -> None | str:
        """Compute ETag with Base85 encoding."""
        if not self.COMPUTE_ETAG:
            return None
        return f'"{hash_bytes(*self._write_buffer)}"'

    def data_received(self, chunk: bytes) -> None | Awaitable[None]:
        """Do nothing."""

    @property
    def dump(self) -> Callable[[Any], str | bytes]:
        """Get the function for dumping the output."""
        if self.content_type in {
            "application/json",
            "application/vnd.asozial.dynload+json",
        }:
            option = ORJSON_OPTIONS
            if self.get_bool_argument("pretty", False):
                option |= json.OPT_INDENT_2
            return lambda spam: json.dumps(spam, option=option)

        if self.content_type == "application/yaml":
            return lambda spam: cast(
                str,
                yaml.dump(
                    spam,
                    width=self.get_int_argument("yaml_width", 80, min_=80),
                ),
            )

        return lambda spam: spam  # type: ignore[no-any-return]

    @property
    def elasticsearch(self) -> AsyncElasticsearch:
        """Get the Elasticsearch client from the settings."""
        return cast(AsyncElasticsearch, self.settings.get("ELASTICSEARCH"))

    @property
    def elasticsearch_prefix(self) -> str:
        """Get the Elasticsearch prefix from the settings."""
        return self.settings.get("ELASTICSEARCH_PREFIX", NAME)

    def finish(
        self, chunk: None | str | bytes | dict[str, Any] = None
    ) -> Future[None]:
        """Finish this response, ending the HTTP request.

        Passing a ``chunk`` to ``finish()`` is equivalent to passing that
        chunk to ``write()`` and then calling ``finish()`` with no arguments.

        Returns a ``Future`` which may optionally be awaited to track the sending
        of the response to the client. This ``Future`` resolves when all the response
        data has been sent, and raises an error if the connection is closed before all
        data can be sent.
        """
        if self._finished:
            raise RuntimeError("finish() called twice")

        if chunk is not None:
            self.write(chunk)

        if (  # pylint: disable=too-many-boolean-expressions
            (content_type := self.content_type)
            and (
                content_type in TEXT_CONTENT_TYPES
                or content_type.startswith("text/")
                or content_type.endswith(("+xml", "+json"))
            )
            and self._write_buffer
            and not self._write_buffer[-1].endswith(b"\n")
        ):
            self.write(b"\n")

        return super().finish()

    def fix_url(  # noqa: C901
        self,
        url: None | str | SplitResult = None,
        new_path: None | str = None,
        **query_args: None | str | bool | float,
    ) -> str:
        """
        Fix a URL and return it.

        If the URL is from another website, link to it with the redirect page,
        otherwise just return the URL with no_3rd_party appended.
        """
        if url is None:
            url = self.request.full_url()
        if isinstance(url, str):
            url = urlsplit(url)
        if url.netloc and url.netloc.lower() != self.request.host.lower():
            url = urlsplit(f"/redirect?to={quote(url.geturl())}")
        path = url.path if new_path is None else new_path  # the path of the url
        if path.startswith("/soundboard/files/") or path in FILE_HASHES_DICT:
            query_args.update(
                no_3rd_party=None,
                theme=None,
                dynload=None,
                openmoji=None,
                bumpscosity=None,
            )
        else:
            query_args.setdefault("no_3rd_party", self.get_no_3rd_party())
            query_args.setdefault("theme", self.get_theme())
            query_args.setdefault("dynload", self.get_dynload())
            query_args.setdefault("openmoji", self.get_openmoji())
            query_args.setdefault("bumpscosity", self.get_bumpscosity())
            if query_args["no_3rd_party"] == self.get_saved_no_3rd_party():
                query_args["no_3rd_party"] = None
            if query_args["theme"] == self.get_saved_theme():
                query_args["theme"] = None
            if query_args["dynload"] == self.get_saved_dynload():
                query_args["dynload"] = None
            if query_args["openmoji"] == self.get_saved_openmoji():
                query_args["openmoji"] = None
            if query_args["bumpscosity"] == self.get_saved_bumpscosity():
                query_args["bumpscosity"] = None

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

    def geoip(
        self,
        ip: None | str = None,  # pylint: disable=invalid-name
        database: str = geoip.__defaults__[0],  # type: ignore
        *,
        allow_fallback: bool = True,
    ) -> Coroutine[None, None, None | dict[str, Any]]:
        """Get GeoIP information."""
        if not ip:
            ip = self.request.remote_ip
        if not EVENT_ELASTICSEARCH.is_set():
            return geoip(ip, database)
        return geoip(
            ip, database, self.elasticsearch, allow_fallback=allow_fallback
        )

    @classmethod
    def get_allowed_methods(cls) -> list[str]:
        """Get allowed methods."""
        methods = {"OPTIONS", *cls.ALLOWED_METHODS}
        if "GET" in cls.ALLOWED_METHODS and cls.supports_head():
            methods.add("HEAD")
        return sorted(methods)

    def get_bool_argument(
        self,
        name: str,
        default: None | bool = None,
    ) -> bool:
        """Get an argument parsed as boolean."""
        if default is not None:
            return str_to_bool(self.get_argument(name, ""), default)
        value = str(self.get_argument(name))
        try:
            return str_to_bool(value)
        except ValueError as err:
            raise HTTPError(400, f"{value} is not a boolean") from err

    def get_bumpscosity(self) -> BumpscosityValue:
        """Get the saved value for the bumpscosity."""
        if spam := self.get_argument("bumpscosity", ""):
            return parse_bumpscosity(spam)
        return self.get_saved_bumpscosity()

    def get_display_theme(self) -> str:
        """Get the theme currently displayed."""
        if "random" not in (theme := self.get_theme()):
            return theme

        ignore_themes = ["random", "random-dark"]

        if theme == "random-dark":
            ignore_themes.extend(("light", "light-blue", "fun"))

        return random.choice(  # nosec: B311
            tuple(theme for theme in THEMES if theme not in ignore_themes)
        )

    def get_dynload(self) -> bool:
        """Return the dynload query argument as boolean."""
        return self.get_bool_argument("dynload", self.get_saved_dynload())

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
                Permission.TRACEBACK
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

    def get_error_page_description(self, status_code: int) -> str:
        """Get the description for the error page."""
        # pylint: disable=too-many-return-statements
        # https://developer.mozilla.org/docs/Web/HTTP/Status
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

    def get_int_argument(
        self,
        name: str,
        default: None | int = None,
        *,
        max_: None | int = None,
        min_: None | int = None,
    ) -> int:
        """Get an argument parsed as integer."""
        if default is None:
            str_value = self.get_argument(name)
            try:
                value = int(str_value, base=0)
            except ValueError as err:
                raise HTTPError(400, f"{str_value} is not an integer") from err
        elif self.get_argument(name, ""):
            try:
                value = int(self.get_argument(name), base=0)
            except ValueError:
                value = default
        else:
            value = default

        if max_ is not None:
            value = min(max_, value)
        if min_ is not None:
            value = max(min_, value)

        return value

    def get_module_infos(self) -> tuple[ModuleInfo, ...]:
        """Get the module infos."""
        return self.settings.get("MODULE_INFOS") or ()

    def get_no_3rd_party(self) -> bool:
        """Return the no_3rd_party query argument as boolean."""
        return self.get_bool_argument(
            "no_3rd_party", self.get_saved_no_3rd_party()
        )

    def get_no_3rd_party_default(self) -> bool:
        """Get the default value for the no_3rd_party param."""
        return self.request.host_name.endswith((".onion", ".i2p"))

    def get_openmoji(self) -> OpenMojiValue:
        """Return the openmoji query argument as boolean."""
        return parse_openmoji_arg(
            self.get_argument("openmoji", ""), self.get_saved_openmoji()
        )

    def get_reporting_api_endpoint(self) -> None | str:
        """Get the endpoint for the Reporting API™️."""
        if not self.settings.get("REPORTING"):
            return None
        endpoint = self.settings.get("REPORTING_ENDPOINT")

        if not endpoint or not endpoint.startswith("/"):
            return endpoint

        return f"{self.request.protocol}://{self.request.host}{endpoint}"

    def get_saved_bumpscosity(self) -> BumpscosityValue:
        """Get the saved value for the bumpscosity."""
        return parse_bumpscosity(self.get_cookie("bumpscosity", ""))

    def get_saved_dynload(self) -> bool:
        """Get the saved value for dynload."""
        return str_to_bool(self.get_cookie("dynload"), False)

    def get_saved_no_3rd_party(self) -> bool:
        """Get the saved value for no_3rd_party."""
        return str_to_bool(
            self.get_cookie("no_3rd_party"), self.get_no_3rd_party_default()
        )

    def get_saved_openmoji(self) -> OpenMojiValue:
        """Get the saved value for openmoji."""
        return parse_openmoji_arg(
            cast(str, self.get_cookie("openmoji", "")), False
        )

    def get_saved_theme(self) -> str:
        """Get the theme saved in the cookie."""
        if (theme := self.get_cookie("theme")) in THEMES:
            return theme
        return "default"

    def get_theme(self) -> str:
        """Get the theme currently selected."""
        if (theme := self.get_argument("theme", None)) in THEMES:
            return theme
        return self.get_saved_theme()

    async def get_time(self) -> datetime:
        """Get the start time of the request in the users timezone."""
        tz: tzinfo = timezone.utc  # pylint: disable=invalid-name
        try:
            geoip = await self.geoip()  # pylint: disable=redefined-outer-name
        except ElasticsearchException:
            LOGGER.exception("Elasticsearch request failed")
            if self.apm_client:
                self.apm_client.capture_exception()
        else:
            if geoip and "timezone" in geoip:
                tz = ZoneInfo(geoip["timezone"])  # pylint: disable=invalid-name
        return datetime.fromtimestamp(
            self.request._start_time, tz=tz  # pylint: disable=protected-access
        )

    def get_user_id(self) -> str:
        """Get the user id saved in the cookie or create one."""
        cookie = self.get_secure_cookie(
            "user_id",
            max_age_days=90,
            min_version=2,
        )

        user_id = cookie.decode("UTF-8") if cookie else str(uuid.uuid4())

        if not self.get_secure_cookie(  # save it in cookie or reset expiry date
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

    def handle_accept_header(
        self, possible_content_types: tuple[str, ...]
    ) -> None:
        """Handle the Accept header and set `self.content_type`."""
        if not possible_content_types:
            return
        content_type = get_best_match(
            self.request.headers.get("Accept") or "*/*",
            possible_content_types,
        )
        if content_type is None:
            self.raise_non_acceptable(possible_content_types)
            return
        self.content_type = content_type
        self.set_content_type_header()

    def head(self, *args: Any, **kwargs: Any) -> None | Awaitable[None]:
        """Handle HEAD requests."""
        if self.get.__module__ == "tornado.web":
            raise HTTPError(405)
        if not self.supports_head():
            raise HTTPError(501)

        kwargs["head"] = True
        return self.get(*args, **kwargs)

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

    def is_authorized(self, permission: Permission) -> None | bool:
        """Check whether the request is authorized."""
        api_secrets: dict[str | None, Permission] = self.settings.get(
            "TRUSTED_API_SECRETS", {}
        )
        auth_secret: str | bytes | None = self.settings.get("AUTH_TOKEN_SECRET")

        def keydecode(token: str) -> None | Permission:
            if auth_secret:
                with contextlib.suppress(InvalidTokenError):
                    return parse_token(token, secret=auth_secret).permissions
            try:
                return api_secrets.get(b64decode(token).decode("UTF-8"))
            except ValueError:
                return None

        permissions: tuple[None | Permission, ...] = (
            *(
                (
                    keydecode(_[7:])
                    if _.lower().startswith("bearer ")
                    else api_secrets.get(_)
                )
                for _ in self.request.headers.get_list("Authorization")
            ),
            *(keydecode(_) for _ in self.get_arguments("access_token")),
            *(api_secrets.get(_) for _ in self.get_arguments("key")),
            keydecode(cast(str, self.get_cookie("access_token", "")))
            if self.ALLOW_COOKIE_AUTHENTICATION
            else None,
            api_secrets.get(self.get_cookie("key", None))
            if self.ALLOW_COOKIE_AUTHENTICATION
            else None,
        )

        if all(perm is None for perm in permissions):
            return None

        result = Permission(0)
        for perm in permissions:
            if perm:
                result |= perm

        return permission in result

    def options(self, *args: Any, **kwargs: Any) -> None:
        """Handle OPTIONS requests."""
        # pylint: disable=unused-argument
        self.set_header("Allow", ", ".join(self.get_allowed_methods()))
        self.set_status(204)
        self.finish()

    def origin_trial(self, token: bytes | str) -> bool:
        """Enable an experimental feature."""
        # pylint: disable=protected-access
        data = b64decode(token)
        payload = json.loads(data[69:])
        origin = urlsplit(payload["origin"])
        url = urlsplit(self.request.full_url())
        if data in self.active_origin_trials:
            return True
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
        self.active_origin_trials.add(data)
        return True

    async def prepare(self) -> None:  # noqa: C901
        """Check authorization and call self.ratelimit()."""
        # pylint: disable=invalid-overridden-method, too-complex, too-many-branches
        if not self.ALLOW_COMPRESSION:
            for transform in self._transforms:
                if isinstance(transform, GZipContentEncoding):
                    # pylint: disable=protected-access
                    transform._gzipping = False

        if crawler_secret := self.settings.get("CRAWLER_SECRET"):
            self.crawler = crawler_secret in self.request.headers.get(
                "User-Agent", ""
            )

        self.now = await self.get_time()
        self.handle_accept_header(self.POSSIBLE_CONTENT_TYPES)

        if self.request.method == "GET":
            if self.redirect_to_canonical_domain():
                return

            if not pytest_is_running() and (
                days := random.randint(0, 31337)  # nosec: B311
            ) in {69, 420, 1337, 31337}:
                self.set_cookie("c", "s", expires_days=days / 24, path="/")

        if self.request.method != "OPTIONS":
            required_permission = self.REQUIRED_PERMISSION
            required_permission_for_method = getattr(
                self, f"REQUIRED_PERMISSION_{self.request.method}", None
            )

            if required_permission is None:
                required_permission = required_permission_for_method
            elif required_permission_for_method is not None:
                required_permission |= required_permission_for_method

            if not (
                required_permission is None
                or (is_authorized := self.is_authorized(required_permission))
            ):
                self.auth_failed = True
                LOGGER.warning(
                    "Unauthorized access to %s from %s",
                    self.request.path,
                    anonymize_ip(self.request.remote_ip),
                )
                raise HTTPError(401 if is_authorized is None else 403)

            if (
                self.MAX_BODY_SIZE is not None
                and len(self.request.body) > self.MAX_BODY_SIZE
            ):
                LOGGER.warning(
                    "%s > MAX_BODY_SIZE (%s)",
                    len(self.request.body),
                    self.MAX_BODY_SIZE,
                )
                raise HTTPError(413)

            if not await self.ratelimit(True):
                await self.ratelimit()

    def raise_non_acceptable(
        self, possible_content_types: tuple[str, ...]
    ) -> None:
        """Only call this if we cannot respect the Accept header."""
        self.clear_header("Content-Type")
        self.set_status(406)
        self.finish("\n".join(possible_content_types) + "\n")

    async def ratelimit(self, global_ratelimit: bool = False) -> bool:
        """Take b1nzy to space using Redis."""
        if (
            not self.settings.get("RATELIMITS")
            or self.request.method == "OPTIONS"
            or self.is_authorized(Permission.RATELIMITS)
            or self.crawler
        ):
            return False

        if not EVENT_REDIS.is_set():
            LOGGER.warning(
                "Ratelimits are enabled, but Redis is not available. "
                "This can happen shortly after starting the website.",
            )
            raise HTTPError(503)

        if global_ratelimit:
            ratelimited, headers = await ratelimit(
                self.redis,
                self.redis_prefix,
                str(self.request.remote_ip),
                bucket=None,
                max_burst=99,  # limit = 100
                count_per_period=20,  # 20 requests per second
                period=1,
                tokens=10 if self.settings.get("UNDER_ATTACK") else 1,
            )
        else:
            method = (
                "GET" if self.request.method == "HEAD" else self.request.method
            )
            if not (limit := getattr(self, f"RATELIMIT_{method}_LIMIT", 0)):
                return False
            ratelimited, headers = await ratelimit(
                self.redis,
                self.redis_prefix,
                str(self.request.remote_ip),
                bucket=getattr(
                    self,
                    f"RATELIMIT_{method}_BUCKET",
                    self.__class__.__name__.lower(),
                ),
                max_burst=limit - 1,
                count_per_period=getattr(  # request count per period
                    self,
                    f"RATELIMIT_{method}_COUNT_PER_PERIOD",
                    30,
                ),
                period=getattr(
                    self, f"RATELIMIT_{method}_PERIOD", 60  # period in seconds
                ),
                tokens=1 if self.request.method != "HEAD" else 0,
            )

        for header, value in headers.items():
            self.set_header(header, value)

        if ratelimited:
            if self.now.date() == date(self.now.year, 4, 20):
                self.set_status(420)
                self.write_error(420)
            else:
                self.set_status(429)
                self.write_error(429)

        return ratelimited

    def redirect_to_canonical_domain(self) -> bool:
        """Redirect to the canonical domain."""
        if (
            not (domain := self.settings.get("DOMAIN"))
            or not self.request.headers.get("Host")
            or self.request.host_name == domain
            or self.request.host_name.endswith((".onion", ".i2p"))
            or regex.fullmatch(r"/[\u2800-\u28FF]+/?", self.request.path)
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

    @property
    def redis(self) -> Redis[str]:
        """Get the Redis client from the settings."""
        return cast("Redis[str]", self.settings.get("REDIS"))

    @property
    def redis_prefix(self) -> str:
        """Get the Redis prefix from the settings."""
        return self.settings.get("REDIS_PREFIX", NAME)

    def set_content_type_header(self) -> None:
        """Set the Content-Type header based on `self.content_type`."""
        if str(self.content_type).startswith("text/"):  # RFC2616 3.7.1
            self.set_header(
                "Content-Type", f"{self.content_type};charset=utf-8"
            )
        elif self.content_type is not None:
            self.set_header("Content-Type", self.content_type)

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

    def set_csp_header(self) -> None:
        """Set the Content-Security-Policy header."""
        script_src = ["'self'"]

        if (
            self.apm_enabled
            and "INLINE_SCRIPT_HASH" in self.settings["ELASTIC_APM"]
        ):
            script_src.extend(
                (
                    f"'sha256-{self.settings['ELASTIC_APM']['INLINE_SCRIPT_HASH']}'",
                    "'unsafe-inline'",  # for browsers that don't support hash
                )
            )

        connect_src = ["'self'"]

        if self.apm_enabled and "SERVER_URL" in self.settings["ELASTIC_APM"]:
            rum_server_url = self.settings["ELASTIC_APM"].get("RUM_SERVER_URL")
            if rum_server_url:
                # the RUM agent needs to connect to rum_server_url
                connect_src.append(rum_server_url)
            elif rum_server_url is None:
                # the RUM agent needs to connect to ["ELASTIC_APM"]["SERVER_URL"]
                connect_src.append(self.settings["ELASTIC_APM"]["SERVER_URL"])

        connect_src.append(  # fix for older browsers
            ("wss" if self.request.protocol == "https" else "ws")
            + f"://{self.request.host}"
        )

        self.set_header(
            "Content-Security-Policy",
            "default-src 'self';"
            f"script-src {' '.join(script_src)};"
            f"connect-src {' '.join(connect_src)};"
            "style-src 'self' 'unsafe-inline';"
            "img-src 'self' https://img.zeit.de https://github.asozial.org;"
            "frame-ancestors 'self';"
            "sandbox allow-downloads allow-same-origin allow-modals"
            " allow-popups-to-escape-sandbox allow-scripts allow-popups"
            " allow-top-navigation-by-user-activation allow-forms;"
            "report-to default;"
            + (
                f"report-uri {self.get_reporting_api_endpoint()};"
                if self.settings.get("REPORTING")
                else ""
            ),
        )

    def set_default_headers(self) -> None:
        """Set default headers."""
        self.set_csp_header()
        self.active_origin_trials = set()
        if self.settings.get("REPORTING"):
            endpoint = self.get_reporting_api_endpoint()
            self.set_header("Reporting-Endpoints", f'default="{endpoint}"')
            self.set_header(
                "Report-To",
                json.dumps(
                    {
                        "group": "default",
                        "max_age": 2592000,
                        "endpoints": [{"url": endpoint}],
                    },
                    option=ORJSON_OPTIONS,
                ),
            )
            self.set_header("NEL", '{"report_to":"default","max_age":2592000}')
        self.set_header("Access-Control-Max-Age", "7200")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header(
            "Access-Control-Allow-Methods",
            ", ".join(self.get_allowed_methods()),
        )
        self.set_header("X-Content-Type-Options", "nosniff")
        self.set_header("Permissions-Policy", "interest-cohort=()")
        self.set_header("Referrer-Policy", "same-origin")
        self.set_header(
            "Cross-Origin-Opener-Policy", "same-origin; report-to=default"
        )
        if self.request.path == "/kaenguru-comics-alt":  # TODO: improve this
            self.set_header(
                "Cross-Origin-Embedder-Policy",
                "credentialless; report-to=default",
            )
        else:
            self.set_header(
                "Cross-Origin-Embedder-Policy",
                "require-corp; report-to=default",
            )
        if self.settings.get("HSTS"):
            self.set_header("Strict-Transport-Security", "max-age=63072000")
        if (
            onion_address := self.settings.get("ONION_ADDRESS")
        ) and not self.request.host_name.endswith(".onion"):
            self.set_header(
                "Onion-Location",
                onion_address
                + self.request.path
                + (f"?{self.request.query}" if self.request.query else ""),
            )
        if self.settings.get("debug"):
            self.set_header("X-Debug", bool_to_str(True))
            for permission in Permission:
                if permission.name:
                    self.set_header(
                        f"X-Permission-{permission.name}",
                        bool_to_str(bool(self.is_authorized(permission))),
                    )
        if self.auth_failed:
            self.set_header("WWW-Authenticate", "Bearer")
        self.origin_trial(
            "AjM7i7vhQFI2RUcab3ZCsJ9RESLDD9asdj0MxpwxHXXtETlsm8dEn+HSd646oPr1dKjn+EcNEj8uV3qFGJzObgsAAAB3eyJvcmlnaW4iOiJodHRwczovL2Fzb3ppYWwub3JnOjQ0MyIsImZlYXR1cmUiOiJTZW5kRnVsbFVzZXJBZ2VudEFmdGVyUmVkdWN0aW9uIiwiZXhwaXJ5IjoxNjg0ODg2Mzk5LCJpc1N1YmRvbWFpbiI6dHJ1ZX0="  # noqa: B950  # pylint: disable=line-too-long, useless-suppression
        )

    @classmethod
    def supports_head(cls) -> bool:
        """Check whether this request handler supports HEAD requests."""
        signature = inspect.signature(cls.get)
        return (
            "head" in signature.parameters
            and signature.parameters["head"].kind
            == inspect.Parameter.KEYWORD_ONLY
        )

    def write(self, chunk: str | bytes | dict[str, Any]) -> None:
        """Write the given chunk to the output buffer.

        To write the output to the network, use the ``flush()`` method.
        """
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")

        self.set_content_type_header()

        if isinstance(chunk, dict):
            chunk = self.dump(chunk)

        if self.now.date() == date(self.now.year, 4, 27):
            if isinstance(chunk, bytes):
                with contextlib.suppress(UnicodeDecodeError):
                    chunk = chunk.decode("UTF-8")
            if isinstance(chunk, str):
                chunk = regex.sub(
                    r"\b\p{Lu}\p{Ll}{4}\p{Ll}*\b",
                    lambda match: "Stanley"
                    if random.Random(match[0]).randrange(5) == self.now.year % 5
                    else match[0],
                    chunk,
                )

        super().write(chunk)
