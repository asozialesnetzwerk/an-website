from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, run_shell

from ansi2html import Ansi2HTMLConverter

def get_handlers():
    return ((r"/host-info/?", Screenfetch),)


class Screenfetch(BaseRequestHandler):
    async def get(self):
        screen_fetch_result = (await run_shell("screenfetch"))[1].decode("utf-8")
        conv = Ansi2HTMLConverter(inline=True)
        html = conv.convert(screen_fetch_result, full=False)
        await self.render(
            "pages/host_info.html",
            screen_fetch=html
        )
