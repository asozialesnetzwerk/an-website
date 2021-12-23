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

from collections.abc import Awaitable

from aioredis import Redis
from tornado.web import HTTPError, RequestHandler


class NimmMalKurzUtils(RequestHandler):
    """The request handler for the room creation API for "Nimm mal kurz!"."""

    def data_received(self, chunk: bytes) -> None | Awaitable[None]:
        pass

    @property
    def redis(self) -> Redis:
        """Return the Redis instance."""
        _r = self.settings.get("REDIS")
        if not _r:
            raise HTTPError(500)  # TODO: Better error handling
        return _r

    async def player_is_owner_of_room(
        self, user_id: str, room_id: str
    ) -> bool:
        """Check if the user is the owner of the room."""
        return user_id == await self.redis.hget(
            self.get_redis_key("room", room_id, "settings"), "owner"
        )

    async def get_room_settings(self, room_id: str):
        """Get the settings for a room."""
        return await self.redis.hgetall(
            self.get_redis_key("room", room_id, "settings")
        )

    def get_redis_key(self, *args):
        """Get the redis key for "Nimm mal kurz!"."""
        prefix = self.settings.get("REDIS_PREFIX")
        if not args:
            return f"{prefix}:nimm-mal-kurz"
        return f"{prefix}:nimm-mal-kurz:{':'.join(args)}"

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

    def get_room_id_specified_by_user(self) -> None | str:
        """Get the room id specified by the user."""
        return self.request.headers.get("X-Room-ID")

    def get_user_id_specified_by_user(self) -> None | str:
        """Get the user id specified by the user."""
        return self.request.headers.get("X-User-ID")

    def get_auth_key_specified_by_user(self) -> None | str:
        """Get the auth key specified by the user."""
        return self.request.headers.get("Authorization")

    async def is_logged_in_as(self, requires_login=False) -> None | str:
        """Check if the user is logged in as a user and return the user id."""
        user_id = self.get_user_id_specified_by_user()
        if not user_id:
            if requires_login:
                raise HTTPError(401, reason="User needs to be logged in.")
            return None
        auth_key = self.get_auth_key_specified_by_user()
        if not auth_key:
            raise HTTPError(401, reason="No authorization key provided.")
        # get the auth token from the user id with redis
        saved_key = await self.redis.get(
            self.get_redis_key("user", user_id, "auth-key")
        )
        if saved_key and saved_key == auth_key:
            return user_id
        raise HTTPError(401, reason="Invalid authorization key.")
