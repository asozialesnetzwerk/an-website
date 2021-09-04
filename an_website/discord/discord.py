# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""A permanent redirect to an invite of the discord guild."""
from __future__ import annotations

import logging

import orjson
import tornado.web
from tornado.httpclient import AsyncHTTPClient, HTTPError

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo

GUILD_ID = 367648314184826880


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/discord/?", Discord),
            (r"/discord/(\d+)/?", Discord),
            (r"/discord/api/?", DiscordApi),
            (r"/discord/api/(\d+)/?", DiscordApi),
        ),
        name="Discord-Einladung",
        description="Eine permanente Einladung zu unserem Discord-Server",
        path="/discord",
    )


async def get_invite(guild_id: int = GUILD_ID) -> tuple[str, str]:
    """
    Get the invite to a discord guild and return it with the source.

    How to get the invite:
        - from the widget (has to be enabled in guild settings)
        - from disboard (the guild needs to set it up first)
    If the invite couldn't be fetched a HTTPError is thrown.
    """
    http_client = AsyncHTTPClient()

    try:  # try getting the invite from the widget
        url = f"https://discord.com/api/guilds/{guild_id}/widget.json"
        response = await http_client.fetch(url)
        response_json = orjson.loads(response.body.decode("utf-8"))
        return response_json["instant_invite"], url
    except HTTPError:
        logging.error(HTTPError)
        try:  # try getting the invite from disboard
            url = f"https://disboard.org/site/get-invite/{guild_id}"
            response = await http_client.fetch(url)
            return orjson.loads(response.body.decode("utf-8")), url
        except HTTPError:
            logging.error(HTTPError)

    raise tornado.web.HTTPError(404, reason="Invite not found.")


class Discord(BaseRequestHandler):
    """The request handler that gets the discord invite and redirects to it."""

    async def get(self, guild_id=GUILD_ID):
        """Get the discord invite and redirect to it."""
        referrer = self.fix_url(
            self.request.headers.get("Referer", default="/")
        )
        self.redirect(
            self.fix_url((await get_invite(guild_id))[0], referrer)
        )


class DiscordApi(APIRequestHandler):
    """The api request handler that gets the discord invite and returns it."""

    async def get(self, guild_id=GUILD_ID):
        """Get the discord invite and render it as json."""
        invite, source_url = await get_invite(guild_id)
        await self.finish(
            {
                "invite": invite,
                "source": source_url
            }
        )
