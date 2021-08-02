"""The uptime page that shows the time the website is running."""
from __future__ import annotations

import datetime
import re
import time

from ..utils.utils import BaseRequestHandler, ModuleInfo

START_TIME = time.time()


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/uptime/?", UptimeHandler),),
        name="Betriebszeit",
        description="Die Dauer die die Webseite am Stück in Betrieb ist.",
        path="/uptime",
    )


class UptimeHandler(BaseRequestHandler):
    """The request handler for the uptime page."""

    async def get(self):
        """Handle the get request and render the page."""
        uptime = datetime.timedelta(seconds=round(time.time() - START_TIME, 3))

        uptime_str = str(uptime)
        uptime_str = re.sub("0{3}$", "", uptime_str, count=1)

        await self.render(
            "pages/uptime.html",
            uptime=uptime_str,
        )
