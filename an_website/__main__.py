import sys

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.httpclient import AsyncHTTPClient

from . import DIR
from .utils.utils import RequestHandlerNotFound, RequestHandlerZeroDivision
from .version.version import Version
from .discord.discord import Discord
from .currency_converter.converter import CurrencyConverter, CurrencyConverterAPI
from .hangman_solver.solver import HangmanSolver, HangmanSolverAPI
from .quotes.quotes import Quotes


AsyncHTTPClient.configure(
    "tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=1000
)


def make_app():
    return Application(
        [
            (r"/error/?", RequestHandlerZeroDivision),
            (r"/version/?", Version),
            (r"/discord/?", Discord),
            (r"/(w(ae|%C3%A4|ä)hrungs-)?rechner/?", CurrencyConverter),
            (r"/(w(ae|%C3%A4|ä)hrungs-)?rechner/api/?", CurrencyConverterAPI),
            (r"/hangman-l(ö|oe|%C3%B6)ser/?", HangmanSolver),
            (r"/hangman-l(ö|oe|%C3%B6)ser/api/?", HangmanSolverAPI),
            (r"/zitate/?", Quotes),
        ],
        # General settings
        autoreload=False,
        compress_response=True,
        debug=bool(sys.flags.dev_mode),
        default_handler_class=RequestHandlerNotFound,
        # Template settings
        template_path=f"{DIR}/templates",
        # Static file settings
        static_path=f"{DIR}/static",
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    IOLoop.current().start()
