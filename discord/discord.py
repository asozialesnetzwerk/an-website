import json
from typing import Optional, Awaitable

from tornado import web
from tornado.httpclient import AsyncHTTPClient, HTTPError

WIDGET_URL = "https://discord.com/api/guilds/367648314184826880/widget.json"


class Discord(web.RequestHandler):
    async def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    async def get(self):
        http_client = AsyncHTTPClient()
        try:
            response = await http_client.fetch(WIDGET_URL)
        except HTTPError:
            self.redirect("https://disboard.org/server/join/367648314184826880")
        else:
            response_json = json.loads(response.body.decode('utf-8'))
            self.redirect(response_json['instant_invite'])
