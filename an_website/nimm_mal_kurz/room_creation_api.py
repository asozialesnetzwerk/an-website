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

from aioredis import Redis
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
        description='Ein Klon des beliebten Karten-Spiels "Halt mal kurz!".',
        keywords=(
            "Halt mal kurz",
            "Nimm mal kurz",
            "Kartenspiel",
        ),
    )


class NimmMalKurzRoomAPI(APIRequestHandler):
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

    @property
    def redis(self) -> Redis:
        """Return the Redis instance."""
        _r = super().redis
        if not _r:
            raise HTTPError(500)  # TODO: Better error handling
        return _r

    async def create_room(self):
        """Create a new room."""
        if self.get_room_id():
            raise HTTPError(
                400,
                "Don't include a room ID in the request when creating a room.",
            )
        # Create room with settings from the request
        room_id = str(uuid.uuid4())
        settings = {
            "name": self.get_argument("name", ""),
            "password": self.get_argument("password", ""),
            "max_players": self.get_argument("max_players", "5"),
            "cards": self.get_argument("cards", "K=10-S|3≤S≤5"),
            "max_time": self.get_argument("max_time", "-1"),
            "max_time_per_card": self.get_argument(
                "max_time_per_card", "30"  # in seconds
            ),
            "owner": self.get_user_id(),
        }
        await self.redis.hset(
            self.get_redis_key("room", room_id, "settings"), mapping=settings
        )

    async def player_is_owner_of_room(
        self, user_id: str, room_id: str
    ) -> bool:
        """Check if the user is the owner of the room."""
        return user_id == await self.redis.hget(
            self.get_redis_key("room", room_id, "settings"), "owner"
        )

    async def join_room(self):
        """Join a room."""
        if not self.get_room_id():
            raise HTTPError(400, reason="No room ID provided.")
        # TODO: Check if user is already in a room
        # if None not in (self.get_room_id()):
        #     raise HTTPError(400, reason="User is currently in a room.")
        room_id = self.get_room_id()
        user_id = await self.get_nmk_user_id()

        player_count = len(
            await self.redis.smembers(
                self.get_redis_key("room", room_id, "users")
            )
        )
        if player_count >= int(
            await self.redis.hget(
                self.get_redis_key("room", room_id, "settings"), "max_players"
            )
        ):
            raise HTTPError(400, reason="Room is full.")

        if _pw := self.redis.hget(  # pw check
            self.get_redis_key("room", room_id, "settings"), "password"
        ):
            if _pw != self.get_argument("password", ""):
                raise HTTPError(400, reason="Wrong password.")

        if not self.redis.sadd(
            self.get_redis_key("room", room_id, "users"),
            user_id,
        ):
            raise HTTPError(500, reason="Could not add user to room.")
        await self.redis.set(
            self.get_redis_key("user", user_id, "room"),
            room_id,
        )
        if not player_count:
            await self.redis.hset(
                self.get_redis_key("room", room_id, "settings"),
                "owner",
                user_id,
            )

        await self.finish({"success": True})

    async def get_room_settings(self, room_id: str):
        """Get the settings for a room."""
        return await self.redis.hgetall(
            self.get_redis_key("room", room_id, "settings")
        )

    async def leave_room(self):
        """Leave the room."""
        user_id, room_id = await self.is_in_room()
        if not (user_id and room_id):
            raise HTTPError(400, reason="User is currently not in a room.")
        users_redis_key = self.get_redis_key("room", room_id, "users")
        if not await self.redis.srem(
            users_redis_key,
            user_id,
        ):
            raise HTTPError(500, reason="Could not remove user from room.")
        await self.redis.delete(self.get_redis_key("user", user_id, "room"))
        # check if user is the last one in the room
        if not self.redis.smembers(users_redis_key):
            # TODO: improve room deletion
            await self.redis.delete(users_redis_key)
            await self.redis.delete(
                self.get_redis_key("room", room_id, "settings")
            )

        # TODO: Do stuff when game is running

        await self.finish({"success": True})

    async def init_websocket(self):
        """
        Init a websocket connection.

        This should be used when in a room.
        """
        room_id = self.get_room_id()
        if not room_id:
            raise HTTPError(400, reason="User is currently not in a room.")
        # TODO: Do websocket stuff

    def get_redis_key(self, *args):
        """Get the redis key for "Nimm mal kurz!"."""
        if not args:
            return f"{self.redis_prefix}:nimm-mal-kurz"
        return f"{self.redis_prefix}:nimm-mal-kurz:{':'.join(args)}"

    def get_room_id(self):
        """Get the room ID from the request headers."""
        return self.request.headers.get("X-Room-ID")

    async def get_nmk_user_id(self) -> str:
        """Get or create the user ID from the request headers."""
        user_id = await self.is_logged_in_as()
        if not user_id:
            return await self.create_user()
        return user_id

    async def is_in_room(self) -> tuple[None, None] | tuple[str, str]:
        """Check if the user is in a room and return user ID with room ID."""
        user_id = await self.is_logged_in_as(True)
        if not user_id:
            return None, None
        # get the room if from the user id with redis
        room_id = await self.redis.get(
            self.get_redis_key("user", user_id, "room")
        )
        if not room_id:
            return None, None
        if await self.redis.sismember(
            self.get_redis_key("room", room_id, "users"),
            user_id,
        ):
            return user_id, room_id
        return None, None

    async def is_logged_in_as(self, requires_login=False) -> None | str:
        """Check if the user is logged in as a user and return the user id."""
        user_id = self.request.headers.get("X-User-ID")
        if not user_id:
            if requires_login:
                raise HTTPError(401, reason="User needs to be logged in.")
            return None
        auth_key = self.request.headers.get("Authorization")
        if not auth_key:
            raise HTTPError(401, reason="No authorization key provided.")
        # get the auth token from the user id with redis
        saved_key = await self.redis.get(
            self.get_redis_key("user", user_id, "auth-key")
        )
        if saved_key and saved_key == auth_key:
            return user_id
        raise HTTPError(401, reason="Invalid authorization key.")

    async def create_user(self) -> str:
        """Create a new user ID, save it to redis, put it in header."""
        self.set_header("X-User-ID", user_id := str(uuid.uuid4()))
        self.set_header("X-User-Auth-Key", auth_key := str(uuid.uuid4()))
        await self.redis.set(
            self.get_redis_key("user", user_id, "auth-key"),
            auth_key,
        )
        return user_id
