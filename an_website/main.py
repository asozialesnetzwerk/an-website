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
# pylint: disable=import-private-name, too-many-lines

"""
The website of the AN.

Loads config and modules and starts Tornado.
"""

from __future__ import annotations

import asyncio
import atexit
import importlib
import logging
import os
import platform
import signal
import ssl
import sys
import threading
import time
import types
import uuid
from asyncio import AbstractEventLoop
from asyncio.runners import _cancel_all_tasks  # type: ignore[attr-defined]
from base64 import b64encode
from collections.abc import Callable, Iterable, Mapping, MutableSequence
from configparser import ConfigParser
from functools import partial
from hashlib import sha256
from multiprocessing.process import _children  # type: ignore[attr-defined]
from pathlib import Path
from socket import socket
from typing import Any, Final, TypedDict, TypeGuard, cast
from warnings import catch_warnings, simplefilter
from zoneinfo import ZoneInfo

import regex
from Crypto.Hash import RIPEMD160
from ecs_logging import StdlibFormatter
from elasticapm.contrib.tornado import ElasticAPM
from redis.asyncio import (
    BlockingConnectionPool,
    Redis,
    SSLConnection,
    UnixDomainSocketConnection,
)
from setproctitle import setproctitle
from tornado.httpserver import HTTPServer
from tornado.log import LogFormatter
from tornado.netutil import bind_sockets, bind_unix_socket
from tornado.process import fork_processes, task_id
from tornado.web import Application, RedirectHandler
from typed_stream import Stream

from . import (
    CA_BUNDLE_PATH,
    DIR,
    EVENT_SHUTDOWN,
    NAME,
    TEMPLATES_DIR,
    UPTIME,
    VERSION,
    pytest_is_running,
)
from .contact.contact import apply_contact_stuff_to_app
from .utils import background_tasks, static_file_handling
from .utils.base_request_handler import BaseRequestHandler, request_ctx_var
from .utils.better_config_parser import BetterConfigParser
from .utils.elasticsearch_setup import setup_elasticsearch
from .utils.logging import WebhookFormatter, WebhookHandler
from .utils.request_handler import NotFoundHandler
from .utils.static_file_from_traversable import TraversableStaticFileHandler
from .utils.template_loader import TemplateLoader
from .utils.utils import (
    ArgparseNamespace,
    Handler,
    ModuleInfo,
    Permission,
    Timer,
    create_argument_parser,
    geoip,
    get_arguments_without_help,
    time_function,
)

try:
    import perf8  # type: ignore[import, unused-ignore]
except ModuleNotFoundError:
    perf8 = None  # pylint: disable=invalid-name

IGNORED_MODULES: Final[set[str]] = {
    "patches",
    "static",
    "templates",
} | (set() if sys.flags.dev_mode or pytest_is_running() else {"example"})

LOGGER: Final = logging.getLogger(__name__)


# add all the information from the packages to a list
# this calls the get_module_info function in every file
# files and dirs starting with '_' get ignored
def get_module_infos() -> str | tuple[ModuleInfo, ...]:
    """Import the modules and return the loaded module infos in a tuple."""
    module_infos: list[ModuleInfo] = []
    loaded_modules: list[str] = []
    errors: list[str] = []

    for potential_module in DIR.iterdir():
        if (
            potential_module.name.startswith("_")
            or potential_module.name in IGNORED_MODULES
            or not potential_module.is_dir()
        ):
            continue

        _module_infos = get_module_infos_from_module(
            potential_module.name, errors, ignore_not_found=True
        )
        if _module_infos:
            module_infos.extend(_module_infos)
            loaded_modules.append(potential_module.name)
            LOGGER.debug(
                (
                    "Found module_infos in %s.__init__.py, "
                    "not searching in other modules in the package."
                ),
                potential_module,
            )
            continue

        if f"{potential_module.name}.*" in IGNORED_MODULES:
            continue

        for potential_file in potential_module.iterdir():
            module_name = f"{potential_module.name}.{potential_file.name[:-3]}"
            if (
                not potential_file.name.endswith(".py")
                or module_name in IGNORED_MODULES
                or potential_file.name.startswith("_")
            ):
                continue
            _module_infos = get_module_infos_from_module(module_name, errors)
            if _module_infos:
                module_infos.extend(_module_infos)
                loaded_modules.append(module_name)

    if len(errors) > 0:
        if sys.flags.dev_mode:
            # exit to make sure it gets fixed
            return "\n".join(errors)
        # don't exit in production to keep stuff running
        LOGGER.error("\n".join(errors))

    LOGGER.info(
        "Loaded %d modules: '%s'",
        len(loaded_modules),
        "', '".join(loaded_modules),
    )

    LOGGER.info(
        "Ignored %d modules: '%s'",
        len(IGNORED_MODULES),
        "', '".join(IGNORED_MODULES),
    )

    sort_module_infos(module_infos)

    # make module_infos immutable so it never changes
    return tuple(module_infos)


def get_module_infos_from_module(
    module_name: str,
    errors: MutableSequence[str],  # gets modified
    ignore_not_found: bool = False,
) -> None | list[ModuleInfo]:
    """Get the module infos based on a module."""
    import_timer = Timer()
    module = importlib.import_module(
        f".{module_name}",
        package="an_website",
    )
    if import_timer.stop() > 0.1:
        LOGGER.warning(
            "Import of %s took %ss. That's affecting the startup time.",
            module_name,
            import_timer.get(),
        )

    module_infos: list[ModuleInfo] = []

    has_get_module_info = "get_module_info" in dir(module)
    has_get_module_infos = "get_module_infos" in dir(module)

    if not (has_get_module_info or has_get_module_infos):
        if ignore_not_found:
            return None
        errors.append(
            f"{module_name} has no 'get_module_info' and no 'get_module_infos' "
            "method. Please add at least one of the methods or add "
            f"'{module_name.rsplit('.', 1)[0]}.*' or {module_name!r} to "
            "IGNORED_MODULES."
        )
        return None

    if has_get_module_info and isinstance(
        module_info := module.get_module_info(),
        ModuleInfo,
    ):
        module_infos.append(module_info)
    elif has_get_module_info:
        errors.append(
            f"'get_module_info' in {module_name} does not return ModuleInfo. "
            "Please fix the returned value."
        )

    if not has_get_module_infos:
        return module_infos or None

    _module_infos = module.get_module_infos()

    if not isinstance(_module_infos, Iterable):
        errors.append(
            f"'get_module_infos' in {module_name} does not return an Iterable. "
            "Please fix the returned value."
        )
        return module_infos or None

    for _module_info in _module_infos:
        if isinstance(_module_info, ModuleInfo):
            module_infos.append(_module_info)
        else:
            errors.append(
                f"'get_module_infos' in {module_name} did return an Iterable "
                f"with an element of type {type(_module_info)}. "
                "Please fix the returned value."
            )

    return module_infos or None


def sort_module_infos(module_infos: list[ModuleInfo]) -> None:
    """Sort a list of module info and move the main page to the top."""
    # sort it so the order makes sense
    module_infos.sort()

    # move the main page to the top
    for i, info in enumerate(module_infos):
        if info.path == "/":
            module_infos.insert(0, module_infos.pop(i))
            break


def get_all_handlers(module_infos: Iterable[ModuleInfo]) -> list[Handler]:
    """
    Parse the module information and return the handlers in a tuple.

    If a handler has only 2 elements a dict with title and description
    gets added. This information is gotten from the module info.
    """
    handler: Handler | list[Any]
    handlers: list[Handler] = static_file_handling.get_handlers()

    # add all the normal handlers
    for module_info in module_infos:
        for handler in module_info.handlers:
            handler = list(handler)  # pylint: disable=redefined-loop-name
            # if the handler is a request handler from us
            # and not a built-in like StaticFileHandler & RedirectHandler
            if issubclass(handler[1], BaseRequestHandler):
                if len(handler) == 2:
                    # set "default_title" or "default_description" to False so
                    # that module_info.name & module_info.description get used
                    handler.append(
                        {
                            "default_title": False,
                            "default_description": False,
                            "module_info": module_info,
                        }
                    )
                else:
                    handler[2]["module_info"] = module_info
            handlers.append(tuple(handler))

    # redirect handler, to make finding APIs easier
    handlers.append((r"/(.+)/api/*", RedirectHandler, {"url": "/api/{0}"}))

    handlers.append(
        (
            r"(?i)/\.well-known/(.*)",
            TraversableStaticFileHandler,
            {
                "root": Path(".well-known"),
                "headers": (("Access-Control-Allow-Origin", "*"),),
            },
        )
    )

    LOGGER.debug("Loaded %d handlers", len(handlers))

    return handlers


def ignore_modules(config: BetterConfigParser) -> None:
    """Read ignored modules from the config."""
    IGNORED_MODULES.update(
        config.getset("GENERAL", "IGNORED_MODULES", fallback=set())
    )


def get_normed_paths_from_module_infos(
    module_infos: Iterable[ModuleInfo],
) -> dict[str, str]:
    """Get all paths from the module infos."""

    def tuple_has_no_none(
        value: tuple[str | None, str | None],
    ) -> TypeGuard[tuple[str, str]]:
        return None not in value

    def info_to_paths(info: ModuleInfo) -> Stream[tuple[str, str]]:
        return (
            Stream(((info.path, info.path),))
            .chain(
                info.aliases.items()
                if isinstance(info.aliases, Mapping)
                else ((alias, info.path) for alias in info.aliases)
            )
            .chain(
                Stream(info.sub_pages)
                .map(lambda sub_info: sub_info.path)
                .filter()
                .map(lambda path: (path, path))
            )
            .filter(tuple_has_no_none)
        )

    return (
        Stream(module_infos)
        .flat_map(info_to_paths)
        .filter(lambda p: p[0].startswith("/"))
        .map(lambda p: (p[0].strip("/").lower(), p[1]))
        .filter(lambda p: p[0])
        .collect(dict)
    )


def make_app(config: ConfigParser) -> str | Application:
    """Create the Tornado application and return it."""
    module_infos, duration = time_function(get_module_infos)
    if isinstance(module_infos, str):
        return module_infos
    if duration > 1:
        LOGGER.warning(
            "Getting the module infos took %ss. That's probably too long.",
            duration,
        )
    handlers = get_all_handlers(module_infos)
    return Application(
        handlers,
        MODULE_INFOS=module_infos,
        SHOW_HAMBURGER_MENU=not Stream(module_infos)
        .exclude(lambda info: info.hidden)
        .filter(lambda info: info.path)
        .empty(),
        NORMED_PATHS=get_normed_paths_from_module_infos(module_infos),
        HANDLERS=handlers,
        # General settings
        autoreload=False,
        debug=sys.flags.dev_mode,
        default_handler_class=NotFoundHandler,
        compress_response=config.getboolean(
            "GENERAL", "COMPRESS_RESPONSE", fallback=False
        ),
        websocket_ping_interval=10,
        # Template settings
        template_loader=TemplateLoader(
            root=TEMPLATES_DIR, whitespace="oneline"
        ),
    )


def apply_config_to_app(app: Application, config: BetterConfigParser) -> None:
    """Apply the config (from the config.ini file) to the application."""
    app.settings["CONFIG"] = config

    app.settings["cookie_secret"] = config.get(
        "GENERAL", "COOKIE_SECRET", fallback="xyzzy"
    )

    app.settings["CRAWLER_SECRET"] = config.get(
        "APP_SEARCH", "CRAWLER_SECRET", fallback=None
    )

    app.settings["DOMAIN"] = config.get("GENERAL", "DOMAIN", fallback=None)

    app.settings["ELASTICSEARCH_PREFIX"] = config.get(
        "ELASTICSEARCH", "PREFIX", fallback=NAME
    )

    app.settings["HSTS"] = config.getboolean("TLS", "HSTS", fallback=False)

    app.settings["NETCUP"] = config.getboolean(
        "GENERAL", "NETCUP", fallback=False
    )

    onion_address = config.get("GENERAL", "ONION_ADDRESS", fallback=None)
    app.settings["ONION_ADDRESS"] = onion_address
    if onion_address is None:
        app.settings["ONION_PROTOCOL"] = None
    else:
        app.settings["ONION_PROTOCOL"] = onion_address.split("://")[0]

    app.settings["RATELIMITS"] = config.getboolean(
        "GENERAL",
        "RATELIMITS",
        fallback=config.getboolean("REDIS", "ENABLED", fallback=False),
    )

    app.settings["REDIS_PREFIX"] = config.get("REDIS", "PREFIX", fallback=NAME)

    app.settings["REPORTING"] = config.getboolean(
        "REPORTING", "ENABLED", fallback=True
    )

    app.settings["REPORTING_BUILTIN"] = config.getboolean(
        "REPORTING", "BUILTIN", fallback=sys.flags.dev_mode
    )

    app.settings["REPORTING_ENDPOINT"] = config.get(
        "REPORTING",
        "ENDPOINT",
        fallback=(
            "/api/reports"
            if app.settings["REPORTING_BUILTIN"]
            else "https://asozial.org/api/reports"
        ),
    )

    app.settings["TRUSTED_API_SECRETS"] = {
        key_perms[0]: Permission(
            int(key_perms[1])
            if len(key_perms) > 1
            else (1 << len(Permission)) - 1  # should be all permissions
        )
        for secret in config.getset(
            "GENERAL", "TRUSTED_API_SECRETS", fallback={"xyzzy"}
        )
        if (key_perms := [part.strip() for part in secret.split("=")])
        if key_perms[0]
    }

    app.settings["AUTH_TOKEN_SECRET"] = config.get(
        "GENERAL", "AUTH_TOKEN_SECRET", fallback=None
    )
    if not app.settings["AUTH_TOKEN_SECRET"]:
        node = uuid.getnode().to_bytes(6, "big")
        secret = RIPEMD160.new(node).digest().decode("BRAILLE")
        LOGGER.warning(
            "AUTH_TOKEN_SECRET is unset, implicitly setting it to %r",
            secret,
        )
        app.settings["AUTH_TOKEN_SECRET"] = secret

    app.settings["UNDER_ATTACK"] = config.getboolean(
        "GENERAL", "UNDER_ATTACK", fallback=False
    )

    apply_contact_stuff_to_app(app, config)


def get_ssl_context(  # pragma: no cover
    config: ConfigParser,
) -> None | ssl.SSLContext:
    """Create SSL context and configure using the config."""
    if config.getboolean("TLS", "ENABLED", fallback=False):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            config.get("TLS", "CERTFILE"),
            config.get("TLS", "KEYFILE", fallback=None),
            config.get("TLS", "PASSWORD", fallback=None),
        )
        return ssl_ctx
    return None


def setup_logging(  # pragma: no cover
    config: ConfigParser,
    force: bool = False,
) -> None:
    """Setup logging."""  # noqa: D401
    root_logger = logging.getLogger()

    if root_logger.handlers:
        if not force:
            return
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

    debug = config.getboolean("LOGGING", "DEBUG", fallback=sys.flags.dev_mode)

    logging.captureWarnings(True)

    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logging.getLogger("tornado.curl_httpclient").setLevel(logging.INFO)
    logging.getLogger("elasticsearch").setLevel(logging.INFO)

    stream_handler = logging.StreamHandler()
    if sys.flags.dev_mode:
        spam = regex.sub(r"%\((end_)?color\)s", "", LogFormatter.DEFAULT_FORMAT)
        formatter = logging.Formatter(spam, LogFormatter.DEFAULT_DATE_FORMAT)
    else:
        formatter = LogFormatter()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    if path := config.get("LOGGING", "PATH", fallback=None):
        os.makedirs(path, 0o755, True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(path, f"{NAME}.log"),
            encoding="UTF-8",
            when="midnight",
            backupCount=30,
            utc=True,
        )
        file_handler.setFormatter(StdlibFormatter())
        root_logger.addHandler(file_handler)


class WebhookLoggingOptions:  # pylint: disable=too-few-public-methods
    """Webhook logging options."""

    __slots__ = (
        "url",
        "content_type",
        "body_format",
        "timestamp_format",
        "timestamp_timezone",
        "escape_message",
        "max_message_length",
    )

    url: str | None
    content_type: str
    body_format: str
    timestamp_format: str | None
    timestamp_timezone: str | None
    escape_message: bool
    max_message_length: int | None

    def __init__(self, config: ConfigParser) -> None:
        """Initialize Webhook logging options."""
        self.url = config.get("LOGGING", "WEBHOOK_URL", fallback=None)
        self.content_type = config.get(
            "LOGGING",
            "WEBHOOK_CONTENT_TYPE",
            fallback="application/json",
        )
        spam = regex.sub(r"%\((end_)?color\)s", "", LogFormatter.DEFAULT_FORMAT)
        self.body_format = config.get(
            "LOGGING",
            "WEBHOOK_BODY_FORMAT",
            fallback='{"text":"' + spam + '"}',
        )
        self.timestamp_format = config.get(
            "LOGGING",
            "WEBHOOK_TIMESTAMP_FORMAT",
            fallback=None,
        )
        self.timestamp_timezone = config.get(
            "LOGGING", "WEBHOOK_TIMESTAMP_TIMEZONE", fallback=None
        )
        self.escape_message = config.getboolean(
            "LOGGING",
            "WEBHOOK_ESCAPE_MESSAGE",
            fallback=True,
        )
        self.max_message_length = config.getint(
            "LOGGING", "WEBHOOK_MAX_MESSAGE_LENGTH", fallback=None
        )


def setup_webhook_logging(  # pragma: no cover
    options: WebhookLoggingOptions,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """Setup Webhook logging."""  # noqa: D401
    if not options.url:
        return

    LOGGER.info("Setting up Webhook logging")

    root_logger = logging.getLogger()

    webhook_content_type = options.content_type
    webhook_handler = WebhookHandler(
        logging.ERROR,
        loop=loop,
        url=options.url,
        content_type=webhook_content_type,
    )
    formatter = WebhookFormatter(
        options.body_format,
        options.timestamp_format,
    )
    formatter.timezone = (
        None
        if options.timestamp_format is None
        else ZoneInfo(options.timestamp_format)
    )
    formatter.escape_message = options.escape_message
    formatter.max_message_length = options.max_message_length
    webhook_handler.setFormatter(formatter)
    root_logger.addHandler(webhook_handler)

    info_handler = WebhookHandler(
        logging.INFO,
        loop=loop,
        url=options.url,
        content_type=webhook_content_type,
    )
    info_handler.setFormatter(formatter)
    logging.getLogger("an_website.quotes.create").addHandler(info_handler)


def setup_apm(app: Application) -> None:  # pragma: no cover
    """Setup APM."""  # noqa: D401
    config: BetterConfigParser = app.settings["CONFIG"]
    app.settings["ELASTIC_APM"] = {
        "ENABLED": config.getboolean("ELASTIC_APM", "ENABLED", fallback=False),
        "SERVER_URL": config.get(
            "ELASTIC_APM", "SERVER_URL", fallback="http://localhost:8200"
        ),
        "SECRET_TOKEN": config.get(
            "ELASTIC_APM", "SECRET_TOKEN", fallback=None
        ),
        "API_KEY": config.get("ELASTIC_APM", "API_KEY", fallback=None),
        "VERIFY_SERVER_CERT": config.getboolean(
            "ELASTIC_APM", "VERIFY_SERVER_CERT", fallback=True
        ),
        "USE_CERTIFI": True,  # doesn't actually use certifi
        "SERVICE_NAME": NAME.removesuffix("-dev"),
        "SERVICE_VERSION": VERSION,
        "ENVIRONMENT": (
            "production" if not sys.flags.dev_mode else "development"
        ),
        "DEBUG": True,
        "CAPTURE_BODY": "errors",
        "TRANSACTION_IGNORE_URLS": [
            "/api/ping",
            "/static/*",
            "/favicon.png",
        ],
        "TRANSACTIONS_IGNORE_PATTERNS": ["^OPTIONS "],
        "PROCESSORS": [
            "an_website.utils.utils.apm_anonymization_processor",
            "elasticapm.processors.sanitize_stacktrace_locals",
            "elasticapm.processors.sanitize_http_request_cookies",
            "elasticapm.processors.sanitize_http_headers",
            "elasticapm.processors.sanitize_http_wsgi_env",
            "elasticapm.processors.sanitize_http_request_body",
        ],
        "RUM_SERVER_URL": config.get(
            "ELASTIC_APM", "RUM_SERVER_URL", fallback=None
        ),
        "RUM_SERVER_URL_PREFIX": config.get(
            "ELASTIC_APM", "RUM_SERVER_URL_PREFIX", fallback=None
        ),
    }

    script_options = [
        f"serviceName:{app.settings['ELASTIC_APM']['SERVICE_NAME']!r}",
        f"serviceVersion:{app.settings['ELASTIC_APM']['SERVICE_VERSION']!r}",
        f"environment:{app.settings['ELASTIC_APM']['ENVIRONMENT']!r}",
    ]

    rum_server_url = app.settings["ELASTIC_APM"]["RUM_SERVER_URL"]

    if rum_server_url is None:
        script_options.append(
            f"serverUrl:{app.settings['ELASTIC_APM']['SERVER_URL']!r}"
        )
    elif rum_server_url:
        script_options.append(f"serverUrl:{rum_server_url!r}")
    else:
        script_options.append("serverUrl:window.location.origin")

    if app.settings["ELASTIC_APM"]["RUM_SERVER_URL_PREFIX"]:
        script_options.append(
            f"serverUrlPrefix:{app.settings['ELASTIC_APM']['RUM_SERVER_URL_PREFIX']!r}"
        )

    app.settings["ELASTIC_APM"]["INLINE_SCRIPT"] = (
        "elasticApm.init({" + ",".join(script_options) + "})"
    )

    app.settings["ELASTIC_APM"]["INLINE_SCRIPT_HASH"] = b64encode(
        sha256(
            app.settings["ELASTIC_APM"]["INLINE_SCRIPT"].encode("ASCII")
        ).digest()
    ).decode("ASCII")

    if app.settings["ELASTIC_APM"]["ENABLED"]:
        app.settings["ELASTIC_APM"]["CLIENT"] = ElasticAPM(app).client


def setup_app_search(app: Application) -> None:  # pragma: no cover
    """Setup Elastic App Search."""  # noqa: D401
    with catch_warnings():
        simplefilter("ignore", DeprecationWarning)
        # pylint: disable-next=import-outside-toplevel
        from elastic_enterprise_search import (  # type: ignore[import-untyped]
            AppSearch,
        )

    config: BetterConfigParser = app.settings["CONFIG"]
    host = config.get("APP_SEARCH", "HOST", fallback=None)
    key = config.get("APP_SEARCH", "SEARCH_KEY", fallback=None)
    verify_certs = config.getboolean(
        "APP_SEARCH", "VERIFY_CERTS", fallback=True
    )
    app.settings["APP_SEARCH"] = (
        AppSearch(
            host,
            bearer_auth=key,
            verify_certs=verify_certs,
            ca_certs=CA_BUNDLE_PATH,
        )
        if host
        else None
    )
    app.settings["APP_SEARCH_HOST"] = host
    app.settings["APP_SEARCH_KEY"] = key
    app.settings["APP_SEARCH_ENGINE"] = config.get(
        "APP_SEARCH", "ENGINE_NAME", fallback=NAME.removesuffix("-dev")
    )


def setup_redis(app: Application) -> None | Redis[str]:
    """Setup Redis."""  # noqa: D401
    config: BetterConfigParser = app.settings["CONFIG"]

    class Kwargs(TypedDict, total=False):
        """Kwargs of BlockingConnectionPool constructor."""

        db: int
        username: None | str
        password: None | str
        retry_on_timeout: bool
        connection_class: type[UnixDomainSocketConnection] | type[SSLConnection]
        path: str
        host: str
        port: int
        ssl_ca_certs: str
        ssl_keyfile: None | str
        ssl_certfile: None | str
        ssl_check_hostname: bool
        ssl_cert_reqs: str

    kwargs: Kwargs = {
        "db": config.getint("REDIS", "DB", fallback=0),
        "username": config.get("REDIS", "USERNAME", fallback=None),
        "password": config.get("REDIS", "PASSWORD", fallback=None),
        "retry_on_timeout": config.getboolean(
            "REDIS", "RETRY_ON_TIMEOUT", fallback=False
        ),
    }
    redis_ssl_kwargs: Kwargs = {
        "connection_class": SSLConnection,
        "ssl_ca_certs": CA_BUNDLE_PATH,
        "ssl_keyfile": config.get("REDIS", "SSL_KEYFILE", fallback=None),
        "ssl_certfile": config.get("REDIS", "SSL_CERTFILE", fallback=None),
        "ssl_cert_reqs": config.get(
            "REDIS", "SSL_CERT_REQS", fallback="required"
        ),
        "ssl_check_hostname": config.getboolean(
            "REDIS", "SSL_CHECK_HOSTNAME", fallback=False
        ),
    }
    redis_host_port_kwargs: Kwargs = {
        "host": config.get("REDIS", "HOST", fallback="localhost"),
        "port": config.getint("REDIS", "PORT", fallback=6379),
    }
    redis_use_ssl = config.getboolean("REDIS", "SSL", fallback=False)
    redis_unix_socket_path = config.get(
        "REDIS", "UNIX_SOCKET_PATH", fallback=None
    )

    if redis_unix_socket_path is not None:
        if redis_use_ssl:
            LOGGER.warning(
                "SSL is enabled for Redis, but a UNIX socket is used"
            )
        if config.has_option("REDIS", "HOST"):
            LOGGER.warning(
                "A host is configured for Redis, but a UNIX socket is used"
            )
        if config.has_option("REDIS", "PORT"):
            LOGGER.warning(
                "A port is configured for Redis, but a UNIX socket is used"
            )
        kwargs.update(
            {
                "connection_class": UnixDomainSocketConnection,
                "path": redis_unix_socket_path,
            }
        )
    else:
        kwargs.update(redis_host_port_kwargs)
        if redis_use_ssl:
            kwargs.update(redis_ssl_kwargs)

    if not config.getboolean("REDIS", "ENABLED", fallback=False):
        app.settings["REDIS"] = None
        return None
    connection_pool = BlockingConnectionPool(
        client_name=NAME,
        decode_responses=True,
        **kwargs,
    )
    redis = cast("Redis[str]", Redis(connection_pool=connection_pool))
    app.settings["REDIS"] = redis
    return redis


def signal_handler(  # noqa: D103  # pragma: no cover
    signalnum: int, frame: None | types.FrameType
) -> None:
    # pylint: disable=unused-argument, missing-function-docstring
    if signalnum in {signal.SIGINT, signal.SIGTERM}:
        EVENT_SHUTDOWN.set()
    if signalnum == getattr(signal, "SIGHUP", None):
        EVENT_SHUTDOWN.set()


def install_signal_handler() -> None:  # pragma: no cover
    """Install the signal handler."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, signal_handler)


def supervise(loop: AbstractEventLoop) -> None:
    """Supervise."""
    while foobarbaz := background_tasks.HEARTBEAT:  # pylint: disable=while-used
        if time.monotonic() - foobarbaz >= 10:
            worker = task_id()
            pid = os.getpid()

            task = asyncio.current_task(loop)
            request = task.get_context().get(request_ctx_var) if task else None

            LOGGER.fatal(
                "Heartbeat timed out for worker %s (pid %d), "
                "current request: %s, current task: %s",
                worker,
                pid,
                request,
                task,
            )
            atexit._run_exitfuncs()  # pylint: disable=protected-access
            os.abort()
        time.sleep(1)


def main(  # noqa: C901  # pragma: no cover
    config: BetterConfigParser | None = None,
) -> int | str:
    """
    Start everything.

    This is the main function that is called when running this program.
    """
    # pylint: disable=too-complex, too-many-branches
    # pylint: disable=too-many-locals, too-many-statements
    setproctitle(NAME)

    install_signal_handler()

    parser = create_argument_parser()
    args, _ = parser.parse_known_args(
        get_arguments_without_help(), ArgparseNamespace()
    )

    if args.version:
        print("Version:", VERSION)
        if args.verbose:
            # pylint: disable-next=import-outside-toplevel
            from .version.version import (
                get_file_hashes,
                get_hash_of_file_hashes,
            )

            print()
            print("Hash der Datei-Hashes:")
            print(get_hash_of_file_hashes())

            if args.verbose > 1:
                print()
                print("Datei-Hashes:")
                print(get_file_hashes())

        return 0

    config = config or BetterConfigParser.from_path(*args.config)
    assert config is not None
    config.add_override_argument_parser(parser)

    setup_logging(config)

    LOGGER.info("Starting %s %s", NAME, VERSION)

    if platform.system() == "Windows":
        LOGGER.warning(
            "Running %s on Windows is not officially supported",
            NAME.removesuffix("-dev"),
        )

    ignore_modules(config)
    app = make_app(config)
    if isinstance(app, str):
        return app

    apply_config_to_app(app, config)
    setup_elasticsearch(app)
    setup_app_search(app)
    setup_redis(app)
    setup_apm(app)

    behind_proxy = config.getboolean("GENERAL", "BEHIND_PROXY", fallback=False)

    server = HTTPServer(
        app,
        body_timeout=3600,
        decompress_request=True,
        max_body_size=1_000_000_000,
        ssl_options=get_ssl_context(config),
        xheaders=behind_proxy,
    )

    socket_factories: list[Callable[[], Iterable[socket]]] = []

    port = config.getint("GENERAL", "PORT", fallback=None)

    if port:
        socket_factories.append(
            partial(
                bind_sockets,
                port,
                "localhost" if behind_proxy else "",
            )
        )

    unix_socket_path = config.get(
        "GENERAL",
        "UNIX_SOCKET_PATH",
        fallback=None,
    )

    if unix_socket_path:
        os.makedirs(unix_socket_path, 0o755, True)
        socket_factories.append(
            lambda: (
                bind_unix_socket(
                    os.path.join(unix_socket_path, f"{NAME}.sock"),
                    mode=0o666,
                ),
            )
        )

    processes = config.getint(
        "GENERAL",
        "PROCESSES",
        fallback=hasattr(os, "fork") * (2 if sys.flags.dev_mode else -1),
    )

    if processes < 0:
        processes = (
            os.process_cpu_count()  # type: ignore[attr-defined]
            if sys.version_info >= (3, 13)
            else os.cpu_count()
        ) or 0

    worker: None | int = None

    run_supervisor_thread = config.getboolean(
        "GENERAL", "SUPERVISE", fallback=False
    )
    elasticsearch_is_enabled = config.getboolean(
        "ELASTICSEARCH", "ENABLED", fallback=False
    )
    redis_is_enabled = config.getboolean("REDIS", "ENABLED", fallback=False)
    webhook_logging_options = WebhookLoggingOptions(config)
    # all config options should be read before forking
    if args.save_config_to:
        with open(args.save_config_to, "w", encoding="UTF-8") as file:
            config.write(file)
    config.set_all_options_should_be_parsed()
    del config
    # show help message if --help is given (after reading config, before forking)
    parser.parse_args()

    if not socket_factories:
        LOGGER.warning("No sockets configured")
        return 0

    # create sockets after checking for --help
    sockets: list[socket] = (
        Stream(socket_factories).flat_map(lambda fun: fun()).collect(list)
    )

    UPTIME.reset()
    main_pid = os.getpid()

    if processes:
        setproctitle(f"{NAME} - Master")

        worker = fork_processes(processes)

        setproctitle(f"{NAME} - Worker {worker}")

        # yeet all children (there should be none, but do it regardless, just in case)
        _children.clear()

        if "an_website.quotes" in sys.modules:
            from .quotes.utils import (  # pylint: disable=import-outside-toplevel
                AUTHORS_CACHE,
                QUOTES_CACHE,
                WRONG_QUOTES_CACHE,
            )

            del AUTHORS_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
            del QUOTES_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
            del WRONG_QUOTES_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
        del geoip.__kwdefaults__["caches"].control.created_by_ultra

        if unix_socket_path:
            sockets.append(
                bind_unix_socket(
                    os.path.join(unix_socket_path, f"{NAME}.{worker}.sock"),
                    mode=0o666,
                )
            )

    # get loop after forking
    # if not forking allow loop to be set in advance by external code
    loop: None | asyncio.AbstractEventLoop
    try:
        with catch_warnings():  # TODO: remove after dropping support for 3.13
            simplefilter("ignore", DeprecationWarning)
            loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = None
    except RuntimeError:
        loop = None

    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if sys.version_info >= (3, 13) and not loop.get_task_factory():
        loop.set_task_factory(asyncio.eager_task_factory)

    if perf8 and "PERF8" in os.environ:
        loop.run_until_complete(perf8.enable())

    setup_webhook_logging(webhook_logging_options, loop)

    server.add_sockets(sockets)

    tasks = background_tasks.start_background_tasks(  # noqa: F841
        module_infos=app.settings["MODULE_INFOS"],
        loop=loop,
        main_pid=main_pid,
        app=app,
        processes=processes,
        elasticsearch_is_enabled=elasticsearch_is_enabled,
        redis_is_enabled=redis_is_enabled,
        worker=worker,
    )

    if run_supervisor_thread:
        background_tasks.HEARTBEAT = time.monotonic()
        threading.Thread(
            target=supervise, args=(loop,), name="supervisor", daemon=True
        ).start()

    try:
        loop.run_forever()
        EVENT_SHUTDOWN.set()
    finally:
        try:  # pylint: disable=too-many-try-statements
            server.stop()
            loop.run_until_complete(asyncio.sleep(1))
            loop.run_until_complete(server.close_all_connections())
            if perf8 and "PERF8" in os.environ:
                loop.run_until_complete(perf8.disable())
            if redis := app.settings.get("REDIS"):
                loop.run_until_complete(
                    redis.aclose(close_connection_pool=True)
                )
            if elasticsearch := app.settings.get("ELASTICSEARCH"):
                loop.run_until_complete(elasticsearch.close())
        finally:
            try:
                _cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                loop.close()
                background_tasks.HEARTBEAT = 0

    return len(tasks)
