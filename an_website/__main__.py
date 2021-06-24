from __future__ import annotations, barry_as_FLUFL

import asyncio
import configparser
import logging
import logging.handlers
import ssl
import sys

import defusedxml
import ecs_logging
import uvloop
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
from tornado.httpclient import AsyncHTTPClient
from tornado.log import LogFormatter
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application

from . import DIR, patches
from .currency_converter import converter
from .discord import discord
from .hangman_solver import solver
from .host_info import host_info
from .kangaroo_soundboard import soundboard
from .quotes import quotes
from .utils import utils
from .version import version

handlers_list = (
    *utils.get_handlers(),
    *version.get_handlers(),
    *discord.get_handlers(),
    *converter.get_handlers(),
    *solver.get_handlers(),
    *quotes.get_handlers(),
    *soundboard.get_handlers(),
    *host_info.get_handlers(),
)


def make_app():
    return Application(
        handlers_list,
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
    root_logger.setLevel(logging.INFO if not sys.flags.dev_mode else logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    if sys.flags.dev_mode:
        stream_handler.setFormatter(logging.Formatter())
    else:
        stream_handler.setFormatter(LogFormatter())
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
        "SECRET_TOKEN": config.get("ELASTIC_APM", "SECRET_TOKEN", fallback=None),
        "API_KEY": config.get("ELASTIC_APM", "API_KEY", fallback=None),
        "SERVICE_NAME": "an-website",
        "SERVICE_VERSION": version.VERSION.strip(),
        "ENVIRONMENT": "production" if not sys.flags.dev_mode else "development",
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
        xheaders=config.getboolean("TORNADO", "BEHIND_PROXY", fallback=False),
        ssl_options=ssl_ctx,
        protocol=config.get("TORNADO", "PROTOCOL", fallback=None),
        decompress_request=True,
    )
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        pass
