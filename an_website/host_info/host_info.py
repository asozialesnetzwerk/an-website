from __future__ import annotations, barry_as_FLUFL

from ..utils.utils import BaseRequestHandler, run_shell


def get_handlers():
    return ((r"/host-info/?", Neofetch),)


class Neofetch(BaseRequestHandler):
    async def get(self):
        self.finish(
            "<pre>"
            + (await run_shell("neofetch --config none --stdout"))[1].decode("utf-8")
            # + (
            #     await run_shell(
            #         "neofetch --config none --color_blocks off | sed -e 's/\\x1b\\[[^m]\\{1,5\\}m//g'"  # pylint: disable=line-too-long
            #     )
            # )[1].decode("utf-8")
            + "<pre/>"
        )  # quick and dirty
