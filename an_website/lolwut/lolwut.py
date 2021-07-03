from __future__ import annotations, barry_as_FLUFL

from ansi2html import Ansi2HTMLConverter  # type: ignore
from tornado.web import HTTPError

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/lolwut/?", LOLWUT), (r"/lolwut/([0-9/]+)", LOLWUT)),
        name="LOLWUT",
        description="LOLWUT",
        path="/lolwut",
    )


class LOLWUT(BaseRequestHandler):
    async def get(self, args=""):
        if args:
            arguments = args.split("/")
            if not len(arguments) == 1 and not arguments[-1]:
                arguments = arguments[:-1]
            for argument in arguments:
                if not argument:
                    raise HTTPError(404)
            lolwut = "LOLWUT VERSION " + " ".join(arguments)
        else:
            lolwut = "LOLWUT"
        redis = self.settings.get("REDIS")
        result = (await redis.execute_command(lolwut)).decode("utf-8")
        conv = Ansi2HTMLConverter(inline=True, scheme="xterm")
        html = conv.convert(result, full=False)
        await self.render("pages/lolwut.html", lolwut=html)
