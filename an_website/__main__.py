"""Website of the AN. Loads config and modules and starts tornado."""
from __future__ import annotations

import asyncio
import configparser
import importlib
import logging
import os
import ssl
import sys
from typing import Optional

import aioredis  # type: ignore
import ecs_logging
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
from elasticsearch import AsyncElasticsearch
from tornado.httpclient import AsyncHTTPClient
from tornado.log import LogFormatter
from tornado.web import Application

from . import DIR, patches
from .utils import utils
from .utils.utils import Handler, HandlerTuple, ModuleInfo
from .version import version

# list of blocked modules
IGNORED_MODULES = ["patches.*", "static.*", "templates.*"]

logger = logging.getLogger(__name__)


# add all the information from the packages to a list
# this calls the get_module_info function in every file
# files/dirs starting with '_' gets ignored
def get_module_infos() -> tuple[ModuleInfo, ...]:
    """Import the modules and return the loaded module infos in a tuple."""
    module_infos: list[ModuleInfo] = []
    loaded_modules: list[str] = []
    errors: list[str] = []
    for (  # pylint: disable=too-many-nested-blocks
        potential_module
    ) in os.listdir(DIR):
        if (
            not potential_module.startswith("_")
            and f"{potential_module}.*" not in IGNORED_MODULES
            and os.path.isdir(f"{DIR}/{potential_module}")
        ):
            for potential_file in os.listdir(f"{DIR}/{potential_module}"):
                module_name = f"{potential_module}.{potential_file[:-3]}"  # pylint: disable=redefined-outer-name
                if (
                    potential_file.endswith(".py")
                    and module_name not in IGNORED_MODULES
                    and not potential_file.startswith("_")
                ):
                    module = importlib.import_module(
                        f".{module_name}",
                        package="an_website",
                    )
                    if "get_module_info" in dir(module):
                        if (
                            (  # check if the annotations specify the return
                                # type as Module info
                                module.get_module_info.__annotations__.get(  # type: ignore
                                    "return", ""
                                )
                                == "ModuleInfo"
                            )
                            # check if returned module_info is type ModuleInfo
                            and isinstance(
                                module_info := module.get_module_info(),  # type: ignore
                                ModuleInfo,
                            )
                        ):
                            module_infos.append(module_info)
                            loaded_modules.append(module_name)
                        else:
                            errors.append(
                                f"'get_module_info' in {DIR}"
                                f"/{potential_module}/{potential_file} does "
                                f"not return ModuleInfo. Please add/fix the "
                                f"return type or add '{potential_module}.*' "
                                f"or '{module_name}' to IGNORED_MODULES."
                            )
                    else:
                        errors.append(
                            f"{DIR}/{potential_module}/{potential_file} has "
                            f"no 'get_module_info' method. Please add the "
                            f"method or add '{potential_module}.*' or "
                            f"'{module_name}' to IGNORED_MODULES."
                        )

    if len(errors) > 0:
        if sys.flags.dev_mode:
            # exit to make sure it gets fixed:
            sys.exit("\n".join(errors))
        else:
            # don't exit in production to keep stuff running:
            logger.error("\n".join(errors))

    logger.info(
        "loaded %d modules: '%s'",
        len(loaded_modules),
        "', '".join(loaded_modules),
    )
    logger.info(
        "ignored %d modules: '%s'",
        len(IGNORED_MODULES),
        "', '".join(IGNORED_MODULES),
    )
    # sort it so the order makes sense.
    module_infos.sort()
    # make it immutable so it never changes:
    return tuple(module_infos)


def get_all_handlers(
    module_infos: tuple[ModuleInfo, ...],
) -> HandlerTuple:
    """
    Parse the module information and return the handlers in a tuple.

    If a handler has only 2 elements a dict with title and description gets
    added. This information is gotten from the module info.
    """
    handlers: list[Handler] = []

    for module_info in module_infos:
        for handler in module_info.handlers:
            if len(handler) == 2:
                # if dict as third arg is needed
                # "title" and "description" have to be specified
                # otherwise the info is taken from the module info
                handler = (
                    handler[0],
                    handler[1],
                    {
                        "title": module_info.name,
                        "description": module_info.description,
                    },
                )
            handlers.append(handler)

    return tuple(handlers)


def make_app() -> Application:
    """Create the tornado application and return it."""
    module_infos: tuple[ModuleInfo, ...] = get_module_infos()
    return Application(
        get_all_handlers(module_infos),  # type: ignore
        MODULE_INFOS=module_infos,
        # General settings
        autoreload=False,
        compress_response=True,
        debug=bool(sys.flags.dev_mode),
        default_handler_class=utils.NotFound,
        websocket_ping_interval=10,
        # Template settings
        template_path=f"{DIR}/templates",
        # Static file settings
        static_path=f"{DIR}/static",
    )


def apply_config_to_app(app: Application, config: configparser.ConfigParser):
    """Apply the config (from the config.ini file) to the application."""
    app.settings["CONFIG"] = config
    app.settings["ELASTIC_APM"] = {
        "ENABLED": config.getboolean("ELASTIC_APM", "ENABLED", fallback=False),
        "SERVER_URL": config.get(
            "ELASTIC_APM", "SERVER_URL", fallback="http://localhost:8200"
        ),
        "SECRET_TOKEN": config.get(
            "ELASTIC_APM", "SECRET_TOKEN", fallback=None
        ),
        "API_KEY": config.get("ELASTIC_APM", "API_KEY", fallback=None),
        "SERVICE_NAME": "an-website",
        "SERVICE_VERSION": version.VERSION.strip(),
        "ENVIRONMENT": "production"
        if not sys.flags.dev_mode
        else "development",
        "DEBUG": True,
        "CAPTURE_BODY": "errors",
    }
    app.settings["ELASTIC_APM_AGENT"] = ElasticAPM(app)
    app.settings["ELASTICSEARCH"] = AsyncElasticsearch(
        cloud_id=config.get("ELASTICSEARCH", "CLOUD_ID", fallback=None),
        host=config.get("ELASTICSEARCH", "HOST", fallback="localhost"),
        port=config.get("ELASTICSEARCH", "PORT", fallback=None),
        url_prefix=config.get("ELASTICSEARCH", "URL_PREFIX", fallback=None),
        use_ssl=config.get("ELASTICSEARCH", "USE_SSL", fallback=False),
        verify_certs=config.getboolean(
            "ELASTICSEARCH", "VERIFY_CERTS", fallback=True
        ),
        http_auth=(
            config.get("ELASTICSEARCH", "USERNAME"),
            config.get("ELASTICSEARCH", "PASSWORD"),
        )
        if config.get("ELASTICSEARCH", "USERNAME", fallback=None)
        and config.get("ELASTICSEARCH", "PASSWORD", fallback=None)
        else None,
        api_key=config.get("ELASTICSEARCH", "API_KEY", fallback=None),
        client_cert=config.get("ELASTICSEARCH", "CLIENT_CERT", fallback=None),
        client_key=config.get("ELASTICSEARCH", "CLIENT_KEY", fallback=None),
        retry_on_timeout=config.get(
            "ELASTICSEARCH", "RETRY_ON_TIMEOUT", fallback=False
        ),
        send_get_body_as=config.get(
            "ELASTICSEARCH", "SEND_GET_BODY_AS", fallback=None
        ),
        http_compress=True,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        headers={
            "accept": "application/vnd.elasticsearch+json; compatible-with=7"
        },
    )
    app.settings["ELASTICSEARCH_PREFIX"] = (
        config.get("ELASTICSEARCH", "PREFIX", fallback="an-website") + "-"
    )
    # sys.exit(
    #     asyncio.get_event_loop().run_until_complete(
    #         app.settings["ELASTICSEARCH"].info()
    #     )
    # )
    app.settings["REDIS"] = aioredis.Redis(
        connection_pool=aioredis.BlockingConnectionPool.from_url(
            config.get("REDIS", "URL", fallback="redis://localhost"),
            db=config.getint("REDIS", "DB", fallback=None),
            username=config.get("REDIS", "USERNAME", fallback=None),
            password=config.get("REDIS", "PASSWORD", fallback=None),
        )
    )
    app.settings["REDIS_PREFIX"] = (
        config.get("REDIS", "PREFIX", fallback="an-website") + ":"
    )
    # sys.exit(
    #     asyncio.get_event_loop()
    #     .run_until_complete(app.settings["REDIS"].execute_command("LOLWUT"))
    #     .decode("utf-8")
    # )


def get_ssl_context(
    config: configparser.ConfigParser,
) -> Optional[ssl.SSLContext]:
    if config.getboolean("SSL", "ENABLED", fallback=False):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            config.get("SSL", "CERTFILE"),
            config.get("SSL", "KEYFILE", fallback=None),
            config.get("SSL", "PASSWORD", fallback=None),
        )
        return ssl_ctx

    return None


def setup_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(
        logging.INFO if not sys.flags.dev_mode else logging.DEBUG
    )
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(
        LogFormatter() if not sys.flags.dev_mode else logging.Formatter()
    )

    root_logger.addHandler(stream_handler)

    if not sys.flags.dev_mode:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            "logs/an-website.log", "midnight", backupCount=7, utc=True
        )
        file_handler.setFormatter(ecs_logging.StdlibFormatter())
        root_logger.addHandler(file_handler)

    logging.captureWarnings(True)


def main():
    patches.apply()
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini")

    setup_logger()

    # read ignored modules from the config
    for module_name in config.get(
        "GENERAL", "IGNORED_MODULES", fallback=""
    ).split(","):
        module_name = module_name.strip()
        if len(module_name) > 0:
            IGNORED_MODULES.append(module_name)

    app = make_app()

    apply_config_to_app(app, config)

    app.listen(
        config.getint("TORNADO", "PORT", fallback=8080),
        protocol=config.get("TORNADO", "PROTOCOL", fallback=None),
        xheaders=config.getboolean("TORNADO", "BEHIND_PROXY", fallback=False),
        decompress_request=True,
        ssl_options=get_ssl_context(config),
    )

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
