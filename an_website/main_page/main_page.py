from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler


def get_handlers():
    return (r"/", MainPage), ("/index.html", MainPage)


class MainPage(BaseRequestHandler):
    async def get(self):
        await self.render("pages/main_page.html")
