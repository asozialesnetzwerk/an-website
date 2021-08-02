"""The wiki with stuff about the AN."""
from __future__ import annotations

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
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
    """The request handler for the wiki page."""

    async def get(self, path):
        """Handle the get requests to the wiki page."""
        return self.render(
            "base.html", content=f"/wiki{path} isn't ready yet."
        )
