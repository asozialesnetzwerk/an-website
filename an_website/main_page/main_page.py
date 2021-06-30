from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/", MainPage), ("/index.html", MainPage)),
        name="Hauptseite",
        description="Die Hauptseite der Webseite",
        path="/"
    )


class MainPage(BaseRequestHandler):
    async def get(self):
        await self.render(
            "pages/main_page.html",
        )
