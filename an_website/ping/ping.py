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

"""The ping API of the website."""

from __future__ import annotations

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/ping", PingPong),),
        name="Ping Pong",
        description="🏓",
        path="/api/ping",
        hidden=True,
    )


class PingPong(APIRequestHandler):
    """The request handler for the ping API."""

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request to the ping API."""
        # pylint: disable=unused-argument
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        await self.finish("🏓")
