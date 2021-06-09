import tornado.ioloop
import tornado.web
from tornado.web import StaticFileHandler

from hangman_solver.solver import HangmanSolver, HangmanSolverApi
from utils.utils import RequestHandlerCustomError
from version.version import Version
from discord.discord import Discord
from currency_converter.converter import CurrencyConverter, CurrencyConverterApi


def make_app():
    return tornado.web.Application([
        ("/version/?", Version),
        ("/discord/?", Discord),
        ("/(waehrungs-)?rechner/?", CurrencyConverter),
        ("/(waehrungs-)?rechner/api/?", CurrencyConverterApi),
        ("/hangman-l(ö|oe)ser/?", HangmanSolver),
        ("/hangman-l(ö|oe)ser/api/?", HangmanSolverApi),
        ("/favicon.ico()", StaticFileHandler, {'path': 'img/favicon.ico'})
    ],
        compress_response=True,
        template_path="templates/",
        default_handler_class=RequestHandlerCustomError
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
