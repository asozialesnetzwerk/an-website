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

"""The website of the AN. Loads config and modules and starts Tornado."""

from __future__ import annotations

import asyncio
import contextlib
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
from asyncio import AbstractEventLoop
from asyncio.runners import _cancel_all_tasks  # type: ignore[attr-defined]
from base64 import b64encode
from collections.abc import Callable, Coroutine, Iterable
from configparser import ConfigParser
from hashlib import sha3_512, sha256
from multiprocessing import process
from pathlib import Path
from typing import Any, Final, cast
from zoneinfo import ZoneInfo

import orjson
import regex
import tornado.netutil
import tornado.process
from ecs_logging import StdlibFormatter
from elastic_enterprise_search import AppSearch  # type: ignore[import]
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore[import]
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import (
    BlockingConnectionPool,
    Redis,
    SSLConnection,
    UnixDomainSocketConnection,
)
from setproctitle import setproctitle
from tornado.httpserver import HTTPServer
from tornado.log import LogFormatter
from tornado.web import Application, RedirectHandler

from . import (
    CONTAINERIZED,
    DIR,
    EVENT_ELASTICSEARCH,
    EVENT_REDIS,
    EVENT_SHUTDOWN,
    NAME,
    TEMPLATES_DIR,
    VERSION,
)
from .contact.contact import apply_contact_stuff_to_app
from .quotes.utils import (
    AUTHORS_CACHE,
    QUOTES_CACHE,
    WRONG_QUOTES_CACHE,
    update_cache_periodically,
)
from .utils import static_file_handling
from .utils.base_request_handler import BaseRequestHandler
from .utils.logging import WebhookFormatter, WebhookHandler
from .utils.request_handler import NotFoundHandler
from .utils.static_file_handling import StaticFileHandler
from .utils.utils import (
    BetterConfigParser,
    Handler,
    ModuleInfo,
    Permission,
    Timer,
    geoip,
    parse_command_line_arguments,
    parse_config,
    time_function,
)

IGNORED_MODULES: Final[set[str]] = {
    "patches.*",
    "static.*",
    "templates.*",
} | (set() if sys.flags.dev_mode else {"example.*"})

LOGGER: Final = logging.getLogger(__name__)

HEARTBEAT: float = 0


# add all the information from the packages to a list
# this calls the get_module_info function in every file
# files and dirs starting with '_' get ignored
def get_module_infos() -> str | tuple[ModuleInfo, ...]:
    """Import the modules and return the loaded module infos in a tuple."""
    module_infos: list[ModuleInfo] = []
    loaded_modules: list[str] = []
    errors: list[str] = []

    for potential_module in os.listdir(DIR):
        if (
            potential_module.startswith("_")
            or f"{potential_module}.*" in IGNORED_MODULES
            or not os.path.isdir(os.path.join(DIR, potential_module))
        ):
            continue

        _module_infos = get_module_infos_from_module(
            potential_module, errors, ignore_not_found=True
        )
        if _module_infos:
            module_infos.extend(_module_infos)
            loaded_modules.append(potential_module)
            LOGGER.debug(
                "Found module_infos in %s.__init__.py, "
                "not searching in other modules in the package.",
                potential_module,
            )
            continue

        for potential_file in os.listdir(os.path.join(DIR, potential_module)):
            module_name = f"{potential_module}.{potential_file[:-3]}"
            if (
                not potential_file.endswith(".py")
                or module_name in IGNORED_MODULES
                or potential_file.startswith("_")
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
    errors: list[str],  # gets modified
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
            import_timer.execution_time,
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
            f"'{module_name.rsplit('.', 1)[0]}.*' or '{module_name}' to "
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


def get_all_handlers(module_infos: tuple[ModuleInfo, ...]) -> list[Handler]:
    """
    Parse the module information and return the handlers in a tuple.

    If a handler has only 2 elements a dict with title and description gets
    added. This information is gotten from the module info.
    """
    handler: Handler | list[Any]
    handlers: list[Handler] = static_file_handling.get_handlers()

    # add all the normal handlers
    for module_info in module_infos:
        for handler in module_info.handlers:
            handler = list(handler)  # pylint: disable=redefined-loop-name
            handler[0] = "(?i)" + handler[0]
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
            handlers.append(tuple(handler))  # type: ignore[arg-type]
        if module_info.path is not None:
            for alias in module_info.aliases:
                handlers.append(
                    (
                        # (?i) -> ignore case
                        # (.*) -> add group that matches anything
                        "(?i)" + alias + "(/.*|)",
                        RedirectHandler,
                        # {0} -> the part after the alias (/.*) or ""
                        {"url": module_info.path + "{0}"},
                    )
                )

    # redirect handler, to make finding APIs easier
    handlers.append((r"(?i)/(.+)/api/*", RedirectHandler, {"url": "/api/{0}"}))

    # redirect from /api to /api/endpunkte (not with alias, because it fails)
    handlers.append((r"(?i)/api/*", RedirectHandler, {"url": "/api/endpunkte"}))

    handlers.append(
        (
            r"(?i)/\.well-known/(.*)",
            StaticFileHandler,
            {"path": ".well-known", "keep_case": True},
        )
    )

    LOGGER.debug("Loaded %d handlers", len(handlers))

    return handlers


def ignore_modules(config: BetterConfigParser) -> None:
    """Read ignored modules from the config."""
    IGNORED_MODULES.update(
        config.getset("GENERAL", "IGNORED_MODULES", fallback="")
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
        handlers,  # type: ignore[arg-type]
        MODULE_INFOS=module_infos,
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
        template_path=TEMPLATES_DIR,
        template_whitespace="oneline",
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

    app.settings["COMMITTERS_URI"] = config.get(
        "GENERAL",
        "COMMITTERS_URI",
        fallback="https://github.asozial.org/an-website/committers.txt",
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
        fallback="/api/reports"
        if app.settings["REPORTING_BUILTIN"]
        else "https://asozial.org/api/reports",
    )

    app.settings["TRUSTED_API_SECRETS"] = {
        key_perms[0]: Permission(
            int(key_perms[1])
            if len(key_perms) > 1
            else (1 << len(Permission)) - 1  # should be all permissions
        )
        for secret in config.getset(
            "GENERAL", "TRUSTED_API_SECRETS", fallback="xyzzy"
        )
        if (key_perms := [part.strip() for part in secret.split("=")])
        if key_perms[0]
    }
    app.settings["AUTH_TOKEN_SECRET"] = (
        config.get("GENERAL", "AUTH_TOKEN_SECRET", fallback=None)
        or sha3_512(__file__.encode("UTF-8")).digest()
    )

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


def setup_webhook_logging(  # pragma: no cover
    config: ConfigParser,
    loop: AbstractEventLoop,
) -> None:
    """Setup WebHook logging."""  # noqa: D401
    if not (webhook_url := config.get("LOGGING", "WEBHOOK_URL", fallback=None)):
        return

    spam = regex.sub(r"%\((end_)?color\)s", "", LogFormatter.DEFAULT_FORMAT)

    root_logger = logging.getLogger()

    webhook_content_type = config.get(
        "LOGGING",
        "WEBHOOK_CONTENT_TYPE",
        fallback="application/json",
    )
    webhook_handler = WebhookHandler(
        logging.ERROR,
        loop=loop,
        url=webhook_url,
        content_type=webhook_content_type,
    )
    formatter = WebhookFormatter(
        config.get(
            "LOGGING",
            "WEBHOOK_BODY_FORMAT",
            fallback='{"text":"' + spam + '"}',
        ),
        config.get(
            "LOGGING",
            "WEBHOOK_TIMESTAMP_FORMAT",
            fallback=None,
        ),
    )
    formatter.timezone = (
        ZoneInfo(config.get("LOGGING", "WEBHOOK_TIMESTAMP_TIMEZONE"))
        if config.has_option("LOGGING", "WEBHOOK_TIMESTAMP_TIMEZONE")
        else None
    )
    formatter.escape_message = config.getboolean(
        "LOGGING",
        "WEBHOOK_ESCAPE_MESSAGE",
        fallback=True,
    )
    webhook_handler.setFormatter(formatter)
    root_logger.addHandler(webhook_handler)


def setup_apm(app: Application) -> None:  # pragma: no cover
    """Setup APM."""  # noqa: D401
    config = app.settings["CONFIG"]
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
        "ENVIRONMENT": "production"
        if not sys.flags.dev_mode
        else "development",
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
        f"serviceName:'{app.settings['ELASTIC_APM']['SERVICE_NAME']}'",
        f"serviceVersion:'{app.settings['ELASTIC_APM']['SERVICE_VERSION']}'",
        f"environment:'{app.settings['ELASTIC_APM']['ENVIRONMENT']}'",
    ]

    rum_server_url = app.settings["ELASTIC_APM"]["RUM_SERVER_URL"]

    if rum_server_url is None:
        script_options.append(
            f"serverUrl:'{app.settings['ELASTIC_APM']['SERVER_URL']}'"
        )
    elif rum_server_url:
        script_options.append(f"serverUrl:'{rum_server_url}'")
    else:
        script_options.append("serverUrl:window.location.origin")

    if app.settings["ELASTIC_APM"]["RUM_SERVER_URL_PREFIX"]:
        script_options.append(
            f"serverUrlPrefix:'{app.settings['ELASTIC_APM']['RUM_SERVER_URL_PREFIX']}'"
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
    config = app.settings["CONFIG"]
    host = config.get("APP_SEARCH", "HOST", fallback=None)
    key = config.get("APP_SEARCH", "SEARCH_KEY", fallback=None)
    app.settings["APP_SEARCH"] = (
        AppSearch(
            host,
            http_auth=key,
            verify_cert=config.getboolean(
                "APP_SEARCH", "VERIFY_CERT", fallback=True
            ),
            ca_certs=os.path.join(DIR, "ca-bundle.crt"),
        )
        if host
        else None
    )
    app.settings["APP_SEARCH_HOST"] = host
    app.settings["APP_SEARCH_KEY"] = key
    app.settings["APP_SEARCH_ENGINE"] = config.get(
        "APP_SEARCH", "ENGINE_NAME", fallback=NAME.removesuffix("-dev")
    )


def setup_elasticsearch(app: Application) -> None | AsyncElasticsearch:
    """Setup Elasticsearch."""  # noqa: D401
    config = app.settings["CONFIG"]
    kwargs = dict(  # noqa: C408
        cloud_id=config.get("ELASTICSEARCH", "CLOUD_ID", fallback=None),
        hosts=tuple(config.getset("ELASTICSEARCH", "HOSTS"))
        if config.has_option("ELASTICSEARCH", "HOSTS")
        else None,
        url_prefix=config.get("ELASTICSEARCH", "URL_PREFIX", fallback=""),
        use_ssl=config.get("ELASTICSEARCH", "USE_SSL", fallback=False),
        verify_certs=config.getboolean(
            "ELASTICSEARCH", "VERIFY_CERTS", fallback=True
        ),
        ca_certs=os.path.join(DIR, "ca-bundle.crt"),
        http_auth=(
            config.get("ELASTICSEARCH", "USERNAME"),
            config.get("ELASTICSEARCH", "PASSWORD"),
        )
        if config.has_option("ELASTICSEARCH", "USERNAME")
        and config.has_option("ELASTICSEARCH", "PASSWORD")
        else None,
        api_key=config.get("ELASTICSEARCH", "API_KEY", fallback=None),
        client_cert=config.get("ELASTICSEARCH", "CLIENT_CERT", fallback=None),
        client_key=config.get("ELASTICSEARCH", "CLIENT_KEY", fallback=None),
        retry_on_timeout=config.get(
            "ELASTICSEARCH", "RETRY_ON_TIMEOUT", fallback=False
        ),
        headers={
            "accept": "application/vnd.elasticsearch+json; compatible-with=7"
        },
    )
    if not config.getboolean("ELASTICSEARCH", "ENABLED", fallback=False):
        app.settings["ELASTICSEARCH"] = None
        return None
    elasticsearch = AsyncElasticsearch(**kwargs)
    app.settings["ELASTICSEARCH"] = elasticsearch
    return elasticsearch


async def check_elasticsearch(app: Application) -> None:  # pragma: no cover
    """Check Elasticsearch."""
    # pylint: disable=invalid-name
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        es: AsyncElasticsearch = cast(
            AsyncElasticsearch, app.settings.get("ELASTICSEARCH")
        )
        try:
            await es.transport.perform_request("HEAD", "/")
        except Exception:  # pylint: disable=broad-except
            EVENT_ELASTICSEARCH.clear()
            LOGGER.exception("Connecting to Elasticsearch failed")
        else:
            if not EVENT_ELASTICSEARCH.is_set():
                try:
                    await setup_elasticsearch_configs(
                        es, app.settings["ELASTICSEARCH_PREFIX"]
                    )
                except Exception:  # pylint: disable=broad-except
                    LOGGER.exception(
                        "An exception occured while configuring Elasticsearch"
                    )
                else:
                    EVENT_ELASTICSEARCH.set()
        await asyncio.sleep(20)


async def setup_elasticsearch_configs(  # noqa: C901
    elasticsearch: AsyncElasticsearch,
    prefix: str,
) -> None:
    """Setup Elasticsearch configs."""  # noqa: D401
    # pylint: disable=too-complex, too-many-branches
    get: Callable[..., Coroutine[None, None, dict[str, Any]]]
    put: Callable[..., Coroutine[None, None, dict[str, Any]]]
    for i in range(3):
        if i == 0:  # pylint: disable=compare-to-zero
            what = "ingest_pipelines"
            get = elasticsearch.ingest.get_pipeline
            put = elasticsearch.ingest.put_pipeline
        elif i == 1:
            what = "component_templates"
            get = elasticsearch.cluster.get_component_template
            put = elasticsearch.cluster.put_component_template
        elif i == 2:
            what = "index_templates"
            get = elasticsearch.indices.get_index_template
            put = elasticsearch.indices.put_index_template

        base_path = Path(os.path.join(DIR, "elasticsearch", what))
        for path in base_path.rglob("*.json"):
            if not path.is_file():
                LOGGER.warning("%s is not a file", path)
                continue

            body = orjson.loads(
                path.read_bytes().replace(b"{prefix}", prefix.encode("ASCII"))
            )

            name = (
                f"{prefix}-{str(path.relative_to(base_path))[:-5].replace('/', '-')}"
            )

            try:
                if what == "ingest_pipelines":
                    current = await get(id=name)
                    current_version = current[name].get("version", 1)
                else:
                    current = await get(
                        name=name,
                        params={"filter_path": f"{what}.name,{what}.version"},
                    )
                    current_version = current[what][0].get("version", 1)
            except NotFoundError:
                current_version = 0

            if current_version < body.get("version", 1):
                if what == "ingest_pipelines":
                    await put(id=name, body=body)
                else:
                    await put(name=name, body=body)
            elif current_version > body.get("version", 1):
                LOGGER.warning(
                    "%s has version %s. The version in Elasticsearch is %s!",
                    path,
                    body.get("version", 1),
                    current_version,
                )


def setup_redis(app: Application) -> None | Redis[str]:
    """Setup Redis."""  # noqa: D401
    config = app.settings["CONFIG"]
    kwargs = {
        "db": config.getint("REDIS", "DB", fallback=0),
        "username": config.get("REDIS", "USERNAME", fallback=None),
        "password": config.get("REDIS", "PASSWORD", fallback=None),
        "retry_on_timeout": config.getboolean(
            "REDIS", "RETRY_ON_TIMEOUT", fallback=False
        ),
        "decode_responses": True,
        "client_name": NAME,
    }
    if config.has_option("REDIS", "UNIX_SOCKET_PATH"):
        kwargs.update(
            {
                "connection_class": UnixDomainSocketConnection,
                "path": config.get("REDIS", "UNIX_SOCKET_PATH"),
            }
        )
    else:
        kwargs.update(
            {
                "host": config.get("REDIS", "HOST", fallback="localhost"),
                "port": config.getint("REDIS", "PORT", fallback=6379),
            }
        )
        if config.getboolean("REDIS", "SSL", fallback=False):
            kwargs.update(
                {
                    "connection_class": SSLConnection,
                    "ssl_ca_certs": os.path.join(DIR, "ca-bundle.crt"),
                    "ssl_keyfile": config.get(
                        "REDIS", "SSL_KEYFILE", fallback=None
                    ),
                    "ssl_certfile": config.get(
                        "REDIS", "SSL_CERTFILE", fallback=None
                    ),
                    "ssl_cert_reqs": config.get(
                        "REDIS", "SSL_CERT_REQS", fallback="required"
                    ),
                    "ssl_check_hostname": config.getboolean(
                        "REDIS", "SSL_CHECK_HOSTNAME", fallback=False
                    ),
                }
            )
    if not config.getboolean("REDIS", "ENABLED", fallback=False):
        app.settings["REDIS"] = None
        return None
    redis: Redis[str] = Redis(connection_pool=BlockingConnectionPool(**kwargs))
    app.settings["REDIS"] = redis
    return redis


async def check_redis(app: Application) -> None:  # pragma: no cover
    """Check Redis."""
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        redis: Redis[str] = cast("Redis[str]", app.settings.get("REDIS"))
        try:
            await redis.ping()
        except Exception:  # pylint: disable=broad-except
            EVENT_REDIS.clear()
            LOGGER.exception("Connecting to Redis failed")
        else:
            EVENT_REDIS.set()
        await asyncio.sleep(20)


async def wait_for_shutdown() -> None:  # pragma: no cover
    """Wait for the shutdown event."""
    loop = asyncio.get_running_loop()
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        await asyncio.sleep(0.05)
    loop.stop()


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


async def heartbeat() -> None:
    """Heartbeat."""
    global HEARTBEAT  # pylint: disable=global-statement
    while HEARTBEAT:  # pylint: disable=while-used
        HEARTBEAT = time.monotonic()
        await asyncio.sleep(0.05)


def supervise() -> None:
    """Supervise."""
    while foobarbaz := HEARTBEAT:  # pylint: disable=while-used
        if time.monotonic() - foobarbaz >= 10:
            task_id = tornado.process.task_id()
            pid = os.getpid()
            LOGGER.fatal(
                "Heartbeat timed out for worker %d (pid %d)", task_id, pid
            )
            with contextlib.suppress(OSError):
                os.kill(pid, getattr(signal, "CTRL_BREAK_EVENT", 9))
        time.sleep(1)


def main(  # noqa: C901
    config: BetterConfigParser | None = None,
) -> None | int | str:  # pragma: no cover
    """
    Start everything.

    This is the main function that is called when running this programm.
    """
    # pylint: disable=too-complex, too-many-branches
    # pylint: disable=too-many-locals, too-many-statements
    global HEARTBEAT  # pylint: disable=global-statement

    setproctitle(NAME)
    install_signal_handler()

    args = parse_command_line_arguments()
    config = parse_config(*args.config) if config is None else config

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

    sockets = []

    ports = {
        *args.port,
        config.getint(
            "GENERAL", "PORT", fallback=8888 if CONTAINERIZED else None
        ),
    }

    for port in ports:
        if port:
            sockets.extend(
                tornado.netutil.bind_sockets(
                    port, "localhost" if behind_proxy else ""
                )
            )

    unix_socket_path = config.get(
        "GENERAL",
        "UNIX_SOCKET_PATH",
        fallback="/data" if CONTAINERIZED else None,
    )

    if unix_socket_path:
        os.makedirs(unix_socket_path, 0o755, True)
        sockets.append(
            tornado.netutil.bind_unix_socket(
                os.path.join(unix_socket_path, f"{NAME}.sock"),
                mode=0o666,
            )
        )

    processes = config.getint(
        "GENERAL",
        "PROCESSES",
        fallback=hasattr(os, "fork") * (2 if sys.flags.dev_mode else -1),
    )

    if processes < 0:
        processes = tornado.process.cpu_count()

    task_id: int | None = None

    if processes and sockets:
        setproctitle(f"{NAME} - Master")

        task_id = tornado.process.fork_processes(processes)

        setproctitle(f"{NAME} - Worker {task_id}")

        # yeet all children (there should be none, but do it regardless, just in case)
        process._children.clear()  # type: ignore[attr-defined]  # pylint: disable=protected-access  # noqa: B950

        del AUTHORS_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
        del QUOTES_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
        del WRONG_QUOTES_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
        del geoip.__kwdefaults__["caches"].control.created_by_ultra

        if unix_socket_path:
            sockets.append(
                tornado.netutil.bind_unix_socket(
                    os.path.join(unix_socket_path, f"{NAME}.{task_id}.sock"),
                    mode=0o666,
                )
            )

    # get loop after forking
    loop = asyncio.get_event_loop_policy().get_event_loop()
    setup_webhook_logging(config, loop)

    _ = asyncio.get_event_loop
    asyncio.get_event_loop = lambda: loop
    server.add_sockets(sockets)
    asyncio.get_event_loop = _

    if sockets:
        # pylint: disable=unused-variable

        task_heartbeat = loop.create_task(heartbeat())  # noqa: F841

        task_shutdown = loop.create_task(wait_for_shutdown())  # noqa: F841

        if config.getboolean("ELASTICSEARCH", "ENABLED", fallback=False):
            task_es = loop.create_task(check_elasticsearch(app))  # noqa: F841

        if config.getboolean("REDIS", "ENABLED", fallback=False):
            task_redis = loop.create_task(check_redis(app))  # noqa: F841

        if not task_id:  # update from one process only
            task_quotes = loop.create_task(  # noqa: F841
                update_cache_periodically(app)
            )

        # pylint: enable=unused-variable

    if config.getboolean("GENERAL", "SUPERVISE", fallback=False) and sockets:
        HEARTBEAT = time.monotonic()
        threading.Thread(
            target=supervise, name="supervisor", daemon=True
        ).start()

    if args.save_config_to:
        with open(args.save_config_to, "w", encoding="UTF-8") as file:
            config.write(file)

    if not sockets:
        return None

    try:
        loop.run_forever()
        EVENT_SHUTDOWN.set()
    finally:
        try:
            server.stop()
            loop.run_until_complete(asyncio.sleep(1))
            loop.run_until_complete(
                asyncio.wait_for(server.close_all_connections(), 5)
            )

            if redis := app.settings.get("REDIS"):
                loop.run_until_complete(
                    asyncio.wait_for(redis.close(close_connection_pool=True), 5)
                )

            if elasticsearch := app.settings.get("ELASTICSEARCH"):
                loop.run_until_complete(
                    asyncio.wait_for(elasticsearch.close(), 5)
                )

        finally:
            try:
                _cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                loop.close()
                HEARTBEAT = 0

    return None
