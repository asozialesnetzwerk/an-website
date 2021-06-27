from __future__ import annotations, barry_as_FLUFL

from ansi2html import Ansi2HTMLConverter  # type: ignore

from .. import DIR
from ..utils.utils import BaseRequestHandler, ModuleInfo, run


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/host-info/?", HostInfo),),
        name="Host-Informationen",
        description="Informationen über den Host-Server dieser Website",
        path="/host-info/",
    )


class HostInfo(BaseRequestHandler):
    async def get(self):
        result = (await run(f"{DIR}/screenfetch"))[1].decode("utf-8")
        conv = Ansi2HTMLConverter(inline=True, scheme="xterm")
        html = conv.convert(result, full=False)
        await self.render("pages/host_info.html", screenfetch=html)
