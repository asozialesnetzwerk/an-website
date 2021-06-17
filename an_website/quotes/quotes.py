from ..utils.utils import RequestHandlerCustomError


class Quotes(RequestHandlerCustomError):
    async def get(self):
        await self.render("pages/quotes.html")
