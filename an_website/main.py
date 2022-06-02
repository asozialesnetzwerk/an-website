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

"""The website of the AN. Loads config and modules and starts Tornado."""

from __future__ import annotations

import asyncio
import configparser
import importlib
import logging
import os
import re
import signal
import ssl
import sys
import types
from collections.abc import Callable, Coroutine
from multiprocessing import process
from pathlib import Path
from typing import Any, cast

import orjson
import tornado.netutil
import tornado.process
from ecs_logging import StdlibFormatter
from elastic_enterprise_search import AppSearch  # type: ignore
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import (
    BlockingConnectionPool,
    Redis,
    SSLConnection,
    UnixDomainSocketConnection,
)
from tornado.httpserver import HTTPServer
from tornado.log import LogFormatter
from tornado.web import Application, RedirectHandler, StaticFileHandler

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
from .quotes import AUTHORS_CACHE, QUOTES_CACHE, WRONG_QUOTES_CACHE
from .utils import static_file_handling
from .utils.request_handler import BaseRequestHandler, NotFoundHandler
from .utils.utils import Handler, ModuleInfo, Permissions, Timer, time_function

IGNORED_MODULES = [
    "patches.*",
    "static.*",
    "templates.*",
    "utils.utils",
    "utils.static_file_handling",
    "swapped_words.sw_config_file",
    "quotes.quotes_image",
    "quotes.share_page",
    "backdoor.backdoor_client",
]

logger = logging.getLogger(__name__)


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

        for potential_file in os.listdir(os.path.join(DIR, potential_module)):
            module_name = f"{potential_module}.{potential_file[:-3]}"
            if (
                not potential_file.endswith(".py")
                or module_name in IGNORED_MODULES
                or potential_file.startswith("_")
            ):
                continue

            import_timer = Timer()
            module = importlib.import_module(
                f".{module_name}",
                package="an_website",
            )

            if "get_module_info" not in dir(module):
                errors.append(
                    f"{os.path.join(DIR, potential_module, potential_file)} "
                    "has no 'get_module_info' method. Please add the method "
                    f"or add '{potential_module}.*' or '{module_name}' to "
                    "IGNORED_MODULES."
                )
                continue

            if isinstance(
                module_info := module.get_module_info(),
                ModuleInfo,
            ):
                module_infos.append(module_info)
                loaded_modules.append(module_name)
                if import_timer.stop() > 0.1:
                    logger.warning(
                        "Import of %s took %ss. "
                        "That's affecting the startup time.",
                        module_name,
                        import_timer.execution_time,
                    )
                continue

            errors.append(
                "'get_module_info' in "
                f"{os.path.join(DIR, potential_module, potential_file)} "
                "does not return ModuleInfo. Please fix the returned value "
                f"or add '{potential_module}.*' or '{module_name}' to "
                "IGNORED_MODULES."
            )

    if len(errors) > 0:
        if sys.flags.dev_mode:
            # exit to make sure it gets fixed
            return "\n".join(errors)
        # don't exit in production to keep stuff running
        logger.error("\n".join(errors))

    logger.info(
        "Loaded %d modules: '%s'",
        len(loaded_modules),
        "', '".join(loaded_modules),
    )

    logger.info(
        "Ignored %d modules: '%s'",
        len(IGNORED_MODULES),
        "', '".join(IGNORED_MODULES),
    )

    sort_module_infos(module_infos)

    # make module_infos immutable so it never changes
    return tuple(module_infos)


def sort_module_infos(module_infos: list[ModuleInfo]) -> None:
    """Sort a list of module info and move the main page to the top."""
    # sort it so the order makes sense
    module_infos.sort()

    # move the main page to the top
    for i, info in enumerate(module_infos):
        if info.path == "/":
            module_infos.insert(0, module_infos.pop(i))
            break


def get_all_handlers(
    module_infos: tuple[ModuleInfo, ...],
) -> list[Handler]:
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
        (r"/.well-known/(.*)", StaticFileHandler, {"path": ".well-known"})
    )

    logger.debug(
        "Loaded %d handlers: %s",
        len(handlers),
        "; ".join(str(handler) for handler in handlers),
    )

    return handlers


def make_app() -> str | Application:
    """Create the Tornado application and return it."""
    module_infos, duration = time_function(get_module_infos)
    if isinstance(module_infos, str):
        return module_infos
    if duration > 1:
        logger.warning(
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
        debug=bool(sys.flags.dev_mode),
        default_handler_class=NotFoundHandler,
        websocket_ping_interval=10,
        # Template settings
        template_path=TEMPLATES_DIR,
    )


def apply_config_to_app(
    app: Application, config: configparser.ConfigParser
) -> None:
    """Apply the config (from the config.ini file) to the application."""
    app.settings["CONFIG"] = config

    app.settings["DOMAIN"] = config.get("GENERAL", "DOMAIN", fallback=None)

    app.settings["HSTS"] = config.get("TLS", "HSTS", fallback=None)

    apply_contact_stuff_to_app(app, config)

    app.settings["cookie_secret"] = config.get(
        "GENERAL", "COOKIE_SECRET", fallback=b"xyzzy"
    )

    app.settings["NETCUP"] = config.getboolean(
        "GENERAL", "NETCUP", fallback=False
    )

    app.settings["TRUSTED_API_SECRETS"] = {
        key_perms[0]: Permissions(
            int(key_perms[1])
            if len(key_perms) > 1
            else (1 << len(Permissions)) - 1  # should be all permissions
        )
        for secret in config.get(
            "GENERAL", "TRUSTED_API_SECRETS", fallback="xyzzy"
        ).split(",")
        if (key_perms := [part.strip() for part in secret.split("=")])
        if key_perms[0]
    }

    onion_address = config.get("GENERAL", "ONION_ADDRESS", fallback=None)
    app.settings["ONION_ADDRESS"] = onion_address
    if onion_address is None:
        app.settings["ONION_PROTOCOL"] = None
    else:
        app.settings["ONION_PROTOCOL"] = onion_address.split("://")[0]

    app.settings["RATELIMITS"] = config.getboolean(
        "GENERAL", "RATELIMITS", fallback=False
    )

    app.settings["REDIS_PREFIX"] = config.get("REDIS", "PREFIX", fallback=NAME)

    app.settings["ELASTICSEARCH_PREFIX"] = config.get(
        "ELASTICSEARCH", "PREFIX", fallback=NAME
    )


def get_ssl_context(
    config: configparser.ConfigParser,
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


def setup_logging(
    config: configparser.ConfigParser, *, testing: bool = False
) -> None:
    """Configure logging."""
    debug = config.getboolean("LOGGING", "DEBUG", fallback=sys.flags.dev_mode)
    path = config.get(
        "LOGGING", "PATH", fallback=None if sys.flags.dev_mode else "logs"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter(
            re.sub(r"%\((end_)?color\)s", "", LogFormatter.DEFAULT_FORMAT),
            LogFormatter.DEFAULT_DATE_FORMAT,
        )
        if sys.flags.dev_mode
        else LogFormatter()
    )
    root_logger.addHandler(stream_handler)

    if not testing and path:
        os.makedirs(path, 0o755, True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(path, f"{NAME}.log"),
            "midnight",
            backupCount=7,
            utc=True,
        )
        file_handler.setFormatter(StdlibFormatter())
        root_logger.addHandler(file_handler)

    logging.captureWarnings(True)

    logging.getLogger("tornado.curl_httpclient").setLevel(logging.INFO)
    logging.getLogger("elasticsearch").setLevel(logging.INFO)

    if testing and not debug:
        logger.setLevel(logging.WARNING)


def setup_apm(app: Application) -> None:
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
    }
    app.settings["ELASTIC_APM_CLIENT"] = ElasticAPM(app).client


def setup_app_search(app: Application) -> None:
    """Setup Elastic App Search."""  # noqa: D401
    config = app.settings["CONFIG"]
    app.settings["APP_SEARCH"] = AppSearch(
        config.get("APP_SEARCH", "HOST", fallback=None),
        http_auth=config.get("APP_SEARCH", "SEARCH_KEY", fallback=None),
        verify_cert=config.getboolean(
            "APP_SEARCH", "VERIFY_CERT", fallback=True
        ),
        ca_certs=os.path.join(DIR, "ca-bundle.crt"),
    )
    app.settings["APP_SEARCH_ENGINE_NAME"] = config.get(
        "APP_SEARCH", "ENGINE_NAME", fallback=NAME.removesuffix("-dev")
    )
    app.settings["APP_SEARCH_SEARCH_KEY"] = config.get(
        "APP_SEARCH", "SEARCH_KEY", fallback=None
    )


def setup_elasticsearch(app: Application) -> None:
    """Setup Elasticsearch."""  # noqa: D401
    config = app.settings["CONFIG"]
    if not config.getboolean("ELASTICSEARCH", "ENABLED", fallback=False):
        app.settings["ELASTICSEARCH"] = None
        return
    app.settings["ELASTICSEARCH"] = AsyncElasticsearch(
        cloud_id=config.get("ELASTICSEARCH", "CLOUD_ID", fallback=None),
        hosts=tuple(
            host.strip()
            for host in config.get("ELASTICSEARCH", "HOSTS").split(",")
        )
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


async def check_elasticsearch(app: Application) -> None:
    """Check Elasticsearch."""
    # pylint: disable=invalid-name
    while True:  # pylint: disable=while-used
        es: AsyncElasticsearch = cast(
            AsyncElasticsearch, app.settings.get("ELASTICSEARCH")
        )
        try:
            await es.info()
        except Exception as exc:  # pylint: disable=broad-except
            EVENT_ELASTICSEARCH.clear()
            logger.exception(exc)
            logger.error("Connecting to Elasticsearch failed!")
        else:
            if not EVENT_ELASTICSEARCH.is_set():
                await setup_elasticsearch_configs(
                    es, app.settings["ELASTICSEARCH_PREFIX"]
                )
            EVENT_ELASTICSEARCH.set()
        await asyncio.sleep(20)


async def setup_elasticsearch_configs(  # noqa: C901
    elasticsearch: AsyncElasticsearch,
    prefix: str,
) -> None:
    # pylint: disable=too-complex, too-many-branches
    """Setup Elasticsearch configs."""  # noqa: D401
    get: Callable[..., Coroutine[Any, Any, dict[str, Any]]]
    put: Callable[..., Coroutine[Any, Any, dict[str, Any]]]
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
                logger.warning("%s is not a file!", path)
                continue

            body = orjson.loads(
                path.read_text("utf-8").replace("{prefix}", prefix)
            )

            name = f"{prefix}-{str(path.relative_to(base_path))[:-5].replace('/', '-')}"

            try:
                if i == 0:  # pylint: disable=compare-to-zero
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
                if i == 0:  # pylint: disable=compare-to-zero
                    await put(id=name, body=body)
                else:
                    await put(name=name, body=body)
            elif current_version > body.get("version", 1):
                logger.warning(
                    "%s has older version %s. Current version is %s!",
                    path,
                    body.get("version", 1),
                    current_version,
                )


def setup_redis(app: Application) -> None:
    """Setup Redis."""  # noqa: D401
    config = app.settings["CONFIG"]
    if not config.getboolean("REDIS", "ENABLED", fallback=False):
        app.settings["REDIS"] = None
        return
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
    app.settings["REDIS"] = Redis(
        connection_pool=BlockingConnectionPool(**kwargs)
    )


async def check_redis(app: Application) -> None:
    """Check Redis."""
    while True:  # pylint: disable=while-used
        redis: Redis = cast(Redis, app.settings.get("REDIS"))  # type: ignore[type-arg]
        try:
            await redis.ping()
        except Exception as exc:  # pylint: disable=broad-except
            EVENT_REDIS.clear()
            logger.exception(exc)
            logger.error("Connecting to Redis failed!")
        else:
            EVENT_REDIS.set()
        await asyncio.sleep(20)


def cancel_all_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel all tasks."""
    tasks = asyncio.all_tasks(loop)
    if not tasks:
        return

    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


async def wait_for_shutdown() -> None:
    """Wait for the shutdown event."""
    loop = asyncio.get_running_loop()
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        await asyncio.sleep(0.1)
    loop.stop()


def signal_handler(  # noqa: D103
    signalnum: int, frame: None | types.FrameType
) -> None:
    # pylint: disable=unused-argument, missing-function-docstring
    if signalnum in {signal.SIGINT, signal.SIGTERM}:
        EVENT_SHUTDOWN.set()


def main() -> None | int | str:  # noqa: C901
    # pylint: disable=too-complex, too-many-branches
    # pylint: disable=too-many-locals, too-many-statements
    """
    Start everything.

    This is the main function that is called when running this file.
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini", encoding="utf-8")

    setup_logging(config)

    logger.info("Starting %s %s", NAME, VERSION)

    if sys.platform == "win32":
        logger.warning(
            "Please note that running on Windows is not officially supported."
        )

    # read ignored modules from the config
    for module_name in config.get(
        "GENERAL", "IGNORED_MODULES", fallback=""
    ).split(","):
        module_name = module_name.strip()  # pylint: disable=redefined-loop-name
        if len(module_name) > 0:
            IGNORED_MODULES.append(module_name)

    app = make_app()
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
        ssl_options=get_ssl_context(config),
        decompress_request=True,
        xheaders=behind_proxy,
    )

    port = config.getint(
        "GENERAL", "PORT", fallback=8888 if CONTAINERIZED else None
    )

    sockets = []

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
        os.makedirs(unix_socket_path, exist_ok=True)
        sockets.append(
            tornado.netutil.bind_unix_socket(
                os.path.join(unix_socket_path, f"{NAME}.sock")
            )
        )

    processes = config.getint(
        "GENERAL",
        "PROCESSES",
        fallback=0
        if sys.flags.dev_mode
        else (tornado.process.cpu_count() if hasattr(os, "fork") else 0),
    )

    if processes > 0:
        tornado.process.fork_processes(processes)
        # yeet all children (there should be none, but do it regardless, just in case)
        process._children.clear()  # type: ignore[attr-defined]  # pylint: disable=protected-access  # noqa: B950
        del AUTHORS_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
        del QUOTES_CACHE.control.created_by_ultra  # type: ignore[attr-defined]
        del WRONG_QUOTES_CACHE.control.created_by_ultra  # type: ignore[attr-defined]

    task_id = tornado.process.task_id()

    if unix_socket_path and task_id is not None:
        sockets.append(
            tornado.netutil.bind_unix_socket(
                os.path.join(unix_socket_path, f"{NAME}.{task_id}.sock")
            )
        )

    server.add_sockets(sockets)

    # pylint: disable=import-outside-toplevel, unused-variable

    loop = asyncio.get_event_loop_policy().get_event_loop()
    wait_for_shutdown_task = loop.create_task(wait_for_shutdown())  # noqa: F841

    if config.getboolean("ELASTICSEARCH", "ENABLED", fallback=False):
        check_es_task = loop.create_task(check_elasticsearch(app))  # noqa: F841

    if config.getboolean("REDIS", "ENABLED", fallback=False):
        check_redis_task = loop.create_task(check_redis(app))  # noqa: F841

    from .quotes import update_cache_periodically

    if not task_id:
        quotes_cache_update_task = loop.create_task(  # noqa: F841
            update_cache_periodically(app)
        )

    try:
        loop.run_forever()
    finally:
        try:
            server.stop()
            loop.run_until_complete(asyncio.sleep(1))
            loop.run_until_complete(server.close_all_connections())
            if redis := app.settings.get("REDIS"):
                loop.run_until_complete(redis.close(close_connection_pool=True))
        finally:
            try:
                cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
            finally:
                loop.close()

    return None
