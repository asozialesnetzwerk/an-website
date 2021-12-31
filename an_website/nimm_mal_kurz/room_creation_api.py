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

"""The room creation API for "Nimm mal kurz!"."""
from __future__ import annotations

import uuid

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo
from .game import GameWebsocket
from .utils import NimmMalKurzUtils


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/api/nimm-mal-kurz/raum/([a-z0-9]+)/", NimmMalKurzRoomAPI),
            (r"/websocket/nimm-mal-kurz/play/", GameWebsocket),
        ),
        name="Nimm mal kurz!",
        description='Ein Klon des beliebten Karten-Spiels "Halt mal kurz!".',
        keywords=(
            "Halt mal kurz",
            "Nimm mal kurz",
            "Kartenspiel",
        ),
    )


class NimmMalKurzRoomAPI(NimmMalKurzUtils, APIRequestHandler):
    """The request handler for the room creation API for "Nimm mal kurz!"."""

    async def post(self, command: str):
        """Handle a GET request."""
        if command == "create":
            await self.create_room()
        elif command == "join":
            await self.join_room()
        elif command == "leave":
            await self.leave_room()
        elif command == "init-websocket":
            await self.init_websocket()
        elif command == "list":
            pass  # await self.list_rooms()
        else:
            raise HTTPError(400)

    async def get_nmk_user_id(self) -> str:
        """Get or create the user ID from the request headers."""
        user_id = await self.is_logged_in_as()
        if not user_id:
            return await self.create_user()
        return user_id

    async def create_user(self) -> str:
        """Create a new user ID, save it to redis, put it in header."""
        self.set_header("X-User-ID", user_id := str(uuid.uuid4()))
        self.set_header("X-User-Auth-Key", auth_key := str(uuid.uuid4()))
        await self.redis.set(
            self.get_redis_key("user", user_id, "auth-key"),
            auth_key,
        )
        return user_id
