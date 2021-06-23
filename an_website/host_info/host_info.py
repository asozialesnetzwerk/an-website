from __future__ import annotations, barry_as_FLUFL

from ansi2html import Ansi2HTMLConverter  # type: ignore

from ..utils.utils import BaseRequestHandler, run_shell


def get_handlers():
    return ((r"/host-info/?", HostInfo),)


class HostInfo(BaseRequestHandler):
    async def get(self):
        screenfetch_result = (await run_shell("screenfetch"))[1].decode("utf-8")
        conv = Ansi2HTMLConverter(inline=True)
        html = conv.convert(screenfetch_result, full=False)
        await self.render("pages/host_info.html", screenfetch=html)
