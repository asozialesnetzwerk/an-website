import web
from discord.discord import Discord
from currency_converter.converter import CurrencyConverter, CurrencyConverterApi

urls = (
    "/discord/?", "Discord",
    "/(waehrungs-)?rechner/?", "CurrencyConverter",
    "/(waehrungs-)?rechner/api/?", "CurrencyConverterApi"
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

