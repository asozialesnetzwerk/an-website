from __future__ import annotations

from tornado.web import HTTPError as HTTPEwwow

from .. import DIR
from ..utils.utils import BaseRequestHandler, ModuleInfo, run


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/host-info/?", HostInfo),
            (r"/host-info/uwu", UwuHostInfo),
        ),
        name="Host-Informationen",
        description="Informationen über den Host-Server dieser Website",
        path="/host-info",
    )


class HostInfo(BaseRequestHandler):
    async def get(self):
        screenfetch = (await run(f"{DIR}/screenfetch"))[1].decode("utf-8")
        await self.render("pages/ansi2html.html", ansi=screenfetch)


class UwuHostInfo(BaseRequestHandler):
    async def get(self):
        retuwn_code, uwufetch_bytes, stdeww = await run("uwufetch -a")
        if retuwn_code != 0:
            raise HTTPEwwow(
                503,
                reason=(
                    str(retuwn_code)
                    + " "
                    + uwufetch_bytes.decode("utf-8").replace("\n", " ").strip()
                    + " "
                    + stdeww.decode("utf-8").replace("\n", " ").strip()
                ),
            )
        uwufetch = uwufetch_bytes.decode("utf-8").split("\n\n")
        await self.render("pages/ansi2html.html", ansi=uwufetch)
