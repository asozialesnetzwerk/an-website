from __future__ import annotations, barry_as_FLUFL

import orjson
from tornado.httpclient import AsyncHTTPClient, HTTPError

from ..utils.utils import BaseRequestHandler, ModuleInfo

WIDGET_URL = "https://discord.com/api/guilds/367648314184826880/widget.json"


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=((r"/discord/?", Discord),),
        name="Discord-Einladung",
        description="Eine permanente Einladung zu unserem Discord-Server",
        path="/discord",
    )


class Discord(BaseRequestHandler):
    async def get(self):
        http_client = AsyncHTTPClient()
        try:
            response = await http_client.fetch(WIDGET_URL)
        except HTTPError:
            self.redirect(
                "https://disboard.org/server/join/367648314184826880"
            )
        else:
            response_json = orjson.loads(response.body.decode("utf-8"))
            self.redirect(response_json["instant_invite"])
