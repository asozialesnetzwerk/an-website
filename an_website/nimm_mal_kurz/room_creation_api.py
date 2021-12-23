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


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/api/nimm-mal-kurz/raum/([a-z0-9]+)/", NimmMalKurzRoomAPI),
        ),
        name="Nimm mal kurz!",
        description="Ein Klon des beliebten Karten-Spiels \"Halt mal kurz!\".",
        keywords=(
            "Halt mal kurz",
            "Nimm mal kurz",
            "Kartenspiel",
        ),
    )


class NimmMalKurzRoomAPI(APIRequestHandler):
    """The request handler for the room creation API for "Nimm mal kurz!"."""

    async def get(self, command: str):
        """Handle a GET request."""
        match command:
            case "create":
                await self.create_room()
            case "join":
                await self.join_room()
            case "leave":
                await self.leave_room()
            case "list":
                await self.list_rooms()
            case "init-websocket":
                await self.init_websocket()
            case _:
                raise HTTPError(404)

    async def prepare(self):
        """Prepare the request handler."""
        if not self.elasticsearch:
            raise HTTPError(500)
        if not self.redis:
            raise HTTPError(500)  # TODO: Better error handling

    def get_redis_key(self, *args):
        """Get the redis key for "Nimm mal kurz!"."""
        if len(args) == 0:
            return f"{self.redis_prefix}:nimm-mal-kurz"
        return f"{self.redis_prefix}:nimm-mal-kurz:{':'.join(args)}"

    def get_room_id(self):
        """Get the room ID from the request headers."""
        return self.request.headers.get("X-Room-ID")

    async def get_user_id(self):
        """Get or create the user ID from the request headers."""
        user_id = self.request.headers.get("X-User-ID")
        if user_id is None:
            return await self.create_user_id()
        return user_id

    async def create_room(self):
        if self.get_room_id():
            return await self.join_room()

    async def join_room(self):
        if not self.get_room_id():
            return await self.create_room()
        pass

    async def is_in_room(self) -> None | str:
        """Check if the user is in a room and return the room id."""
        user_id = await self.get_user_id()
        if not user_id:
            return None
        # get the room if from the user id with redis
        room_id = await self.elasticsearch.search(
            index="nimm-mal-kurz",
            body={
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "user_id": user_id,
                                },
                            },
                        ],
                    },
                },
            },
        )
        if not room_id:
            return None

    async def leave_room(self):
        pass

    async def list_rooms(self):
        pass

    async def init_websocket(self):
        """
        Init a websocket connection.

        This should be used when in a room.
        """

    async def create_user_id(self) -> str:
        self.set_header("X-User-ID", _id := str(uuid.uuid4()))
        return _id
