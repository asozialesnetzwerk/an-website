from __future__ import annotations, barry_as_FLUFL

import asyncio
import configparser
import importlib
import logging
import logging.handlers
import os
import ssl
import sys
from typing import Any, List, Tuple

import defusedxml  # type: ignore
import ecs_logging
import uvloop
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
from tornado.httpclient import AsyncHTTPClient
from tornado.log import LogFormatter
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application

from . import DIR, patches
from .utils import utils
from .version import version

# list of blocked modules
BLOCK_LIST = ("patches.*",)


# add all the tornado handlers from the packages to a list
# this calls the get_handlers function in every file
# stuff starting with '_' gets ignored
def get_all_handlers():
    handlers_list: List[Tuple[str, Any, ...]] = []
    errors: List[str] = []
    loaded_modules: List[str] = []
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
                    if "get_handlers" in dir(module):
                        loaded_modules.append(module_name)
                        handlers_list += module.get_handlers()  # type: ignore
                    else:
                        errors.append(
                            f"{DIR}/{potential_module}/{potential_file} "
                            f"has no 'get_handlers' method. Please add the "
                            f"method or add '{potential_module}.*' or "
                            f"'{module_name}' to BLOCK_LIST."
                        )

    if len(errors) > 0:
        if sys.flags.dev_mode:
            # exit to make sure it gets fixed:
            sys.exit("\n".join(errors))
        else:
            # don't exit in production to keep stuff running:
            root_logger.warning("\n".join(errors))

    root_logger.info(
        "loaded %d modules: %s", len(loaded_modules), ", ".join(loaded_modules)
    )

    return handlers_list


def make_app():
    return Application(
        get_all_handlers(),
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
    app = make_app()
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
    apm = ElasticAPM(app)
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
