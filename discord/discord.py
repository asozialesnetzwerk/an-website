import requests
import web

widget_url = "https://discord.com/api/guilds/367648314184826880/widget.json"


class Discord:
    def GET(self):
        response = requests.get(widget_url)
        if response.status_code == 200:
            web.seeother(response.json()["instant_invite"])
        else:
            return web.seeother("https://disboard.org/server/join/367648314184826880")
