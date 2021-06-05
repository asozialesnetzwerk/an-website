from typing import Optional, Awaitable

import requests
from tornado import web

widget_url = "https://discord.com/api/guilds/367648314184826880/widget.json"


class Discord(web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        response = requests.get(widget_url)
        if response.status_code == 200:
            self.redirect(url=response.json()["instant_invite"])
        else:
            self.redirect(url="https://disboard.org/server/join/367648314184826880")
