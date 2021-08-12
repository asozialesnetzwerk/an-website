"""A permanent redirect to an invite of the discord guild."""
from __future__ import annotations

import orjson
from tornado.httpclient import AsyncHTTPClient, HTTPError

from ..utils.utils import BaseRequestHandler, ModuleInfo

WIDGET_URL = "https://discord.com/api/guilds/367648314184826880/widget.json"


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/discord/?", Discord),),
        name="Discord-Einladung",
        description="Eine permanente Einladung zu unserem Discord-Server",
        path="/discord",
    )


class Discord(BaseRequestHandler):
    """The request handler that gets the discord invite and redirects to it."""

    async def get(self):
        """Get the discord invite and redirect to it."""
        http_client = AsyncHTTPClient()

        referrer = self.fix_url(
            self.request.headers.get("Referer", default="/")
        )
        try:
            response = await http_client.fetch(WIDGET_URL)
        except HTTPError:
            print()
            self.redirect(
                self.fix_url(
                    "https://disboard.org/server/join/367648314184826880",
                    referrer,
                )
            )
        else:
            response_json = orjson.loads(response.body.decode("utf-8"))
            self.redirect(
                self.fix_url(response_json["instant_invite"], referrer)
            )
