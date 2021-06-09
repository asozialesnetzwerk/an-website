import tornado.ioloop
import tornado.web
from tornado.web import StaticFileHandler

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
