import json

from tornado.httpclient import AsyncHTTPClient, HTTPError

from utils.utils import RequestHandlerCustomError

WIDGET_URL = "https://discord.com/api/guilds/367648314184826880/widget.json"


class Discord(RequestHandlerCustomError):
    async def get(self):
        http_client = AsyncHTTPClient()
        try:
            response = await http_client.fetch(WIDGET_URL)
        except HTTPError:
            self.redirect("https://disboard.org/server/join/367648314184826880")
        else:
            response_json = json.loads(response.body.decode('utf-8'))
            self.redirect(response_json['instant_invite'])
