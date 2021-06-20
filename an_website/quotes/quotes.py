from __future__ import annotations

from ..utils.utils import BaseRequestHandler


def get_handlers():
    return ((r"/zitate/?", Quotes),)


class Quotes(BaseRequestHandler):
    async def get(self):
        await self.render("pages/quotes.html")
