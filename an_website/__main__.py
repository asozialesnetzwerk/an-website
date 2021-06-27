from __future__ import annotations, barry_as_FLUFL

import asyncio
import configparser
import importlib
import logging
import os
import ssl
import sys
from typing import List

import defusedxml  # type: ignore
import ecs_logging
import uvloop
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
from elasticsearch import AsyncElasticsearch
from tornado.httpclient import AsyncHTTPClient
from tornado.log import LogFormatter
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application

from an_website.utils.utils import Handler

from . import DIR, patches
from .utils import utils
from .version import version

# list of blocked modules
BLOCK_LIST = ("patches.*", "static.*", "templates.*")


# add all the information from the packages to a list
# this calls the get_module_info function in every file
# files/dirs starting with '_' gets ignored
def get_module_infos() -> List[utils.ModuleInfo]:
    module_info_list: List[utils.ModuleInfo] = []
    loaded_modules: List[str] = []
    errors: List[str] = []
    for potential_module in os.listdir(DIR):
        if (
            not potential_module.startswith("_")
            and f"{potential_module}.*" not in BLOCK_LIST
            and os.path.isdir(f"{DIR}/{potential_module}")
        ):
            for potential_file in os.listdir(f"{DIR}/{potential_module}"):
                module_name = f"{potential_module}.{potential_file[:-3]}"
                if (
                    potential_file.endswith(".py")
                    and module_name not in BLOCK_LIST
                    and not potential_file.startswith("_")
                ):
                    module = importlib.import_module(
                        f".{module_name}",
                        package="an_website",
                    )
                    if "get_module_info" in dir(module):
                        module_info_list.append(
                            module.get_module_info()  # type: ignore
                        )
                        loaded_modules.append(module_name)
                    else:
                        errors.append(
                            f"{DIR}/{potential_module}/{potential_file} has "
                            f"no 'get_module_info' method. Please add the "
                            f"method or add '{potential_module}.*' or "
                            f"'{module_name}' to BLOCK_LIST."
                        )

    if len(errors) > 0:
        if sys.flags.dev_mode:
            # exit to make sure it gets fixed:
            sys.exit("\n".join(errors))
        else:
            # don't exit in production to keep stuff running:
            root_logger.error("\n".join(errors))

    root_logger.info(
        "loaded %d modules: %s",
        len(loaded_modules),
        ", ".join(loaded_modules),
    )

    return module_info_list


def get_all_handlers(
    module_info_list: List[utils.ModuleInfo],
) -> List[Handler]:
    handlers_list: List[Handler] = []

    for module_info in module_info_list:
        handlers_list += module_info.handlers

    return handlers_list


def make_app(module_info_list: List[utils.ModuleInfo]):
    return Application(
        get_all_handlers(module_info_list),  # type: ignore
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
        # module information:
        module_info_list=module_info_list
    )


if __name__ == "__main__":
    patches.apply()
    defusedxml.defuse_stdlib()
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

    app = make_app(get_module_infos())
    config = configparser.ConfigParser(interpolation=None)
    config.BOOLEAN_STATES = {"sure": True, "nope": False}  # type: ignore
    config.read("config.ini")
    app.settings["CONFIG"] = config
    app.settings["ELASTIC_APM"] = {
        "ENABLED": config.getboolean("ELASTIC_APM", "ENABLED", fallback=False),
        "SERVER_URL": config.get("ELASTIC_APM", "SERVER_URL", fallback=None),
        "SECRET_TOKEN": config.get(
            "ELASTIC_APM", "SECRET_TOKEN", fallback=None
        ),
        "API_KEY": config.get("ELASTIC_APM", "API_KEY", fallback=None),
        "SERVICE_NAME": "an-website",
        "SERVICE_VERSION": version.VERSION.strip(),
        "ENVIRONMENT": "production"
        if not sys.flags.dev_mode
        else "development",
    }
    app.settings["ELASTIC_APM_AGENT"] = ElasticAPM(app)
    app.settings["ELASTICSEARCH"] = AsyncElasticsearch(
        hosts=[config.get("ELASTICSEARCH", "HOST", fallback=None)],
        verify_certs=config.getboolean(
            "ELASTICSEARCH", "VERIFY_CERTS", fallback=True
        ),
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
    )
    app.settings["ELASTICSEARCH_PREFIX"] = config.get(
        "ELASTICSEARCH", "PREFIX", fallback="an-website-"
    )
    try:
        AsyncHTTPClient.configure(
            "tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=1000
        )
    except ModuleNotFoundError:
        if not sys.flags.dev_mode:
            raise
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    AsyncIOMainLoop().install()
    if config.getboolean("SSL", "ENABLED", fallback=False):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(
            config.get("SSL", "CERTFILE"),
            config.get("SSL", "KEYFILE", fallback=None),
            config.get("SSL", "PASSWORD", fallback=None),
        )
    else:
        ssl_ctx = None  # type: ignore  # pylint: disable=invalid-name
    app.listen(
        config.getint("TORNADO", "PORT", fallback=8080),
        protocol=config.get("TORNADO", "PROTOCOL", fallback=None),
        xheaders=config.getboolean("TORNADO", "BEHIND_PROXY", fallback=False),
        decompress_request=True,
        ssl_options=ssl_ctx,
    )
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
