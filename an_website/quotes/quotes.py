from ..utils.utils import RequestHandlerCustomError


def get_handlers() -> tuple:
    return r"/zitate/?", Quotes


class Quotes(RequestHandlerCustomError):
    async def get(self):
        await self.render("pages/quotes.html")
