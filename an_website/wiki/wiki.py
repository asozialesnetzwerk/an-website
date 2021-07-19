from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (
                r"/wiki(/?.*)",
                WikiHandler,
            ),
        ),
        name="Asoziales Wiki",
        description="Ein Wiki mit Sachen des Asozialen Netzwerkes.",
        path="/wiki",
    )


class WikiHandler(BaseRequestHandler):
    async def get(self, path):
        return self.finish(f"/wiki{path} isn't ready yet.")
