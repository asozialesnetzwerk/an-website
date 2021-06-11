import sys

import tornado.ioloop
import tornado.web

from utils.utils import RequestHandlerNotFound, RequestHandlerDivideByZero
from version.version import Version
from discord.discord import Discord
from currency_converter.converter import CurrencyConverter, CurrencyConverterAPI
from hangman_solver.solver import HangmanSolver, HangmanSolverAPI


def make_app():
    return tornado.web.Application([
        (r"/error/?", RequestHandlerDivideByZero),
        (r"/version/?", Version),
        (r"/discord/?", Discord),
        (r"/(w(ae|%C3%A4|ä)hrungs-)?rechner/?", CurrencyConverter),
        (r"/(w(ae|%C3%A4|ä)hrungs-)?rechner/api/?", CurrencyConverterAPI),
        (r"/hangman-l(ö|oe|%C3%B6)ser/?", HangmanSolver),
        (r"/hangman-l(ö|oe|%C3%B6)ser/api/?", HangmanSolverAPI)
    ],
        # General settings
        autoreload=False,
        compress_response=True,
        debug=bool(sys.flags.dev_mode),
        default_handler_class=RequestHandlerNotFound,
        # Template settings
        template_path="templates/",
        # Static file settings
        static_path="static/"
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
