from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/", MainPage), ("/index.html", MainPage)),
        name="Hauptseite",
        description="Die Hauptseite der Wesbeite",
    )


class MainPage(BaseRequestHandler):
    async def get(self):
        base_url = "/".join(self.get_url().split("/")[:-1])
        print("/".join(self.get_url().split("/")[:-1]))
        await self.render(
            "pages/main_page.html",
            module_infos=self.settings.get("module_info_list"),
            base_url=base_url,
        )
