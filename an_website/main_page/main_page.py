"""The main page of the website."""
from __future__ import annotations

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        # the empty dict prevents the header from being changed
        handlers=((r"/", MainPage, {}), ("/index.html", MainPage, {})),
        name="Hauptseite",
        description="Die Hauptseite der Webseite",
        path="/",
    )


class MainPage(BaseRequestHandler):
    """The request handler of the main page."""

    async def get(self):
        """Handle the get requests and display the main page."""
        await self.render(
            "pages/main_page.html",
        )
