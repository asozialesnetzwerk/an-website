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

"""A permanent redirect to an invite of the Discord guild."""
from __future__ import annotations

import os
import time

import orjson as json
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from .. import DIR as ROOT_DIR
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo

GUILD_ID = "367648314184826880"

INVITE_CACHE: dict[
    str,
    tuple[float, str, str] | tuple[float, HTTPError],
] = {}


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/discord", ANDiscord),
            (r"/api/discord", ANDiscordAPI),
            (f"/api/discord/({GUILD_ID})", ANDiscordAPI),
            (r"/api/discord/(\d+)", DiscordAPI),
        ),
        name="Discord-Einladung",
        short_name="Discord",
        description="Eine permanente Einladung zu unserer Discord-Gilde",
        path="/discord",
        keywords=(
            "Discord",
            "Server",
            "Guild",
            "Gilde",
            "Invite",
            "Einladung",
        ),
    )


async def url_returns_200(url: str) -> bool:
    """Check whether a URL returns a status code of 200."""
    response = await AsyncHTTPClient().fetch(
        url,
        method="HEAD",
        raise_error=False,
        ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
    )
    return response.code == 200


async def get_invite(guild_id: str = GUILD_ID) -> tuple[str, str]:
    """
    Get the invite to a Discord guild and return it with the source.

    How to get the invite:
        - from the widget (has to be enabled in guild settings)
        - from DISBOARD (the guild needs to set it up first)
    If the invite couldn't be fetched an HTTPError is raised.
    """
    reason = "Invite not found."

    # try getting the invite from the widget
    url = f"https://discord.com/api/guilds/{guild_id}/widget.json"
    response = await AsyncHTTPClient().fetch(
        url, raise_error=False, ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt")
    )
    if response.code == 200:
        response_json = json.loads(response.body)
        invite = response_json["instant_invite"]
        if invite is not None:
            return invite, url
        reason = f"No instant invite in widget ({url}) found."

    # try getting the invite from DISBOARD
    url = f"https://disboard.org/site/get-invite/{guild_id}"
    response = await AsyncHTTPClient().fetch(
        url, raise_error=False, ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt")
    )
    if response.code == 200:
        return (
            json.loads(response.body),
            f"https://disboard.org/server/{guild_id}",
        )

    # check if Top.gg lists the guild
    url = f"https://top.gg/servers/{guild_id}/join"
    if await url_returns_200(url):
        return url, f"https://top.gg/servers/{guild_id}/"

    # check if Discords.com lists the guild
    if await url_returns_200(
        # API endpoint that only returns 200 if the guild exists
        f"https://discords.com/api-v2/server/{guild_id}/relevant"
    ):
        return (
            f"https://discords.com/servers/{guild_id}/join",
            f"https://discords.com/servers/{guild_id}/",
        )

    raise HTTPError(404, reason=reason)


async def get_invite_with_cache(
    guild_id: str = GUILD_ID,
) -> tuple[str, str]:
    """Get an invite from cache or from get_invite()."""
    if guild_id in INVITE_CACHE:
        cache_entry = INVITE_CACHE[guild_id]
        if cache_entry[0] > time.monotonic() - 300:
            if isinstance(cache_entry[1], HTTPError):
                raise cache_entry[1]
            return cache_entry[1], cache_entry[2]

    try:
        invite, source = await get_invite(guild_id)
    except HTTPError as exc:
        INVITE_CACHE[guild_id] = (time.monotonic(), exc)
        raise exc

    INVITE_CACHE[guild_id] = (time.monotonic(), invite, source)

    return invite, source


class ANDiscord(HTMLRequestHandler):
    """The request handler that gets the Discord invite and redirects to it."""

    RATELIMIT_GET_LIMIT = 10

    async def get(self, *, head: bool = False) -> None:
        """Get the Discord invite."""
        invite = (await get_invite_with_cache(GUILD_ID))[0]
        if head:
            return
        return await self.render(
            "pages/ask_for_redirect.html",
            redirect_url=invite,
            from_url=None,
            discord=True,
        )


class DiscordAPI(APIRequestHandler):
    """The API request handler that gets the Discord invite and returns it."""

    RATELIMIT_GET_LIMIT = 5
    RATELIMIT_GET_COUNT_PER_PERIOD = 10  # 10 requests per minute

    async def get(
        self, guild_id: str = GUILD_ID, *, head: bool = False
    ) -> None:
        """Get the Discord invite and render it as JSON."""
        if head:
            return
        invite, source_url = await get_invite_with_cache(guild_id)
        return await self.finish({"invite": invite, "source": source_url})


class ANDiscordAPI(DiscordAPI):
    """The API request handler only for the AN Discord guild."""

    RATELIMIT_GET_LIMIT = 10
    RATELIMIT_GET_COUNT_PER_PERIOD = 30  # 30 requests per minute
