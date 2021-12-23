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

"""A subtle clone of the card game "Halt mal kurz!"."""
from __future__ import annotations

from typing import Awaitable, Optional

import orjson as json
import tornado.websocket

from .utils import NimmMalKurzUtils


class GameWebsocket(tornado.websocket.WebSocketHandler, NimmMalKurzUtils):
    """The Websocket handler."""

    user_id: None | str = None
    room_id: None | str = None
    auth_key: None | str = None

    async def open(self, *args):
        print("WebSocket opened")

    async def on_message(self, message):
        print("WebSocket message:", message)
        json_message = json.loads(message)
        if not (self.user_id and self.room_id and self.auth_key):
            self.user_id = json_message.get("user_id")
            self.room_id = json_message.get("room_id")
            self.auth_key = json_message.get("auth_key")
            user_id, room_id = await self.is_in_room()
            if user_id and room_id:
                return self.write_message(json.dumps({"success": True}))
            return self.write_message(json.dumps({"success": False}))
        # TODO: Handle more commands

    async def on_close(self):
        print("WebSocket closed")

    def data_received(self, chunk: bytes) -> None | Awaitable[None]:
        pass

    def get_room_id_specified_by_user(self) -> None | str:
        """Get the room id specified by the user."""
        return self.room_id

    def get_user_id_specified_by_user(self) -> None | str:
        """Get the user id specified by the user."""
        return self.user_id

    def get_auth_key_specified_by_user(self) -> None | str:
        """Get the auth key specified by the user."""
        return self.auth_key
