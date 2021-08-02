"""The page that displays the redis version."""
from __future__ import annotations

from tornado.web import HTTPError

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/lolwut/?", LOLWUT), (r"/lolwut/([0-9/]+)", LOLWUT)),
        name="LOLWUT",
        description="LOLWUT; präsentiert von Redis",
        path="/lolwut",
    )


class LOLWUT(BaseRequestHandler):
    """The request handler for the LOLWUT page."""

    async def get(self, args=""):
        """Handle get requests to the LOLWUT page."""
        if args:
            arguments = args.split("/")
            if not len(arguments) == 1 and not arguments[-1]:
                arguments = arguments[:-1]
            for argument in arguments:
                if not argument:
                    raise HTTPError(404)
            command = "LOLWUT VERSION " + " ".join(arguments)
        else:
            command = "LOLWUT"
        redis = self.settings.get("REDIS")
        lolwut = (await redis.execute_command(command)).decode("utf-8")
        await self.render("pages/ansi2html.html", ansi=lolwut)
