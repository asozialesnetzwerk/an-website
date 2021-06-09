import sys

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
        ("/(waehrungs-)?rechner/api/?", CurrencyConverterApi)
    ],
        # General settings
        autoreload=False
        compress_response=True,
        debug=bool(sys.flags.dev_mode)
        default_handler_class=RequestHandlerCustomError,
        # Template settings
        template_path="templates/",
        # Static file settings
        static_path="static/"
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
