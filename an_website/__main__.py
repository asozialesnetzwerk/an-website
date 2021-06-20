from __future__ import annotations

import configparser
import logging
import logging.handlers
import sys

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.httpclient import AsyncHTTPClient
from elasticapm.contrib.tornado import ElasticAPM  # type: ignore
import ecs_logging

from . import DIR
from .utils import utils
from .version import version
from .discord import discord
from .currency_converter import converter
from .hangman_solver import solver
from .quotes import quotes
from .kangaroo_soundboard import soundboard

handlers_list = (
    *soundboard.get_handlers(),
    *quotes.get_handlers(),
    *utils.get_handlers(),
    *version.get_handlers(),
    *discord.get_handlers(),
    *converter.get_handlers(),
    *solver.get_handlers(),
)


def make_app():
    return Application(
        handlers_list,
        # General settings
        autoreload=False,
        compress_response=True,
        debug=bool(sys.flags.dev_mode),
        default_handler_class=utils.NotFound,
        # Template settings
        template_path=f"{DIR}/templates",
        # Static file settings
        static_path=f"{DIR}/static",
    )


if __name__ == "__main__":
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if not sys.flags.dev_mode else logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s:%(name)s:%(message)s")
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
    app.listen(8080)
    try:
        IOLoop.current().start()
    except KeyboardInterrupt:
        pass
