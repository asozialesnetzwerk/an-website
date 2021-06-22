from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, run_shell


def get_handlers():
    return ((r"/host-info/?", Neofetch),)


class Neofetch(BaseRequestHandler):
    async def get(self):
        self.finish(
            "<pre>"
            + (await run_shell("screenfetch -N"))[1].decode("utf-8")
            + "<pre/>"
        )  # quick and dirty
