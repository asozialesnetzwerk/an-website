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
