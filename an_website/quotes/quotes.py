from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/zitate/?", Quotes),),
        name="Falsch zugeordnete Zitate",
        description="Eine Website mit falsch zugeordneten Zitaten",
        path="/zitate",
    )


class Quotes(BaseRequestHandler):
    async def get(self):
        await self.render("pages/quotes.html")
