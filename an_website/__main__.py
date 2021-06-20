import sys
from typing import List

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.httpclient import AsyncHTTPClient

from . import DIR
from .utils import utils
from .version import version
from .discord import discord
from .currency_converter import converter
from .hangman_solver import solver
from .quotes import quotes
from .kangaroo_soundboard import soundboard

AsyncHTTPClient.configure(
    "tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=1000
)

handlers_list: List[tuple] = [
    *soundboard.get_handlers(),
    quotes.get_handler(),
    utils.get_handler(),
    version.get_handler(),
    discord.get_handler(),
    *converter.get_handlers(),
    *solver.get_handlers(),
]


def make_app():
    return Application(
        handlers_list,
        # General settings
        autoreload=False,
        compress_response=True,
        debug=bool(sys.flags.dev_mode),
        default_handler_class=utils.RequestHandlerNotFound,
        # Template settings
        template_path=f"{DIR}/templates",
        # Static file settings
        static_path=f"{DIR}/static",
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    IOLoop.current().start()
