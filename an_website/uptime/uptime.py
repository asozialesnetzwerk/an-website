from __future__ import annotations, barry_as_FLUFL

import datetime
import re
import time

from ..utils.utils import BaseRequestHandler, ModuleInfo

START_TIME = time.time()


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/version/?", Version),),
        name="Betriebszeit",
        description="Die Dauer die die Webseite am Stück in Betrieb ist.",
        path="/version",
    )


class Version(BaseRequestHandler):
    async def get(self):
        uptime = datetime.timedelta(seconds=round(time.time() - START_TIME, 3))

        uptime_str = str(uptime)
        uptime_str = re.sub("0{3}$", "", uptime_str, count=1)

        await self.render(
            "pages/uptime.html",
            uptime=uptime_str,
        )
