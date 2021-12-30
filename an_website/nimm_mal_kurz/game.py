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

import os
import uuid
from typing import Any

import orjson as json
import tornado.websocket as websocket
from aioredis import Redis
from argon2 import PasswordHasher
from elasticsearch import AsyncElasticsearch
from names_generator import generate_name
from tornado.web import HTTPError

PH = PasswordHasher()  # nicht die Webseite


class GameWebsocket(websocket.WebSocketHandler):
    """The Websocket handler."""

    user_id: None | str = None
    room_id: None | str = None

    async def open(self, *args) -> None:
        print("WebSocket opened")

    async def on_message(self, message) -> None:
        print("WebSocket message:", message)
        json_message = json.loads(message)

        command = json_message.get("command")
        if not command:
            await self.write_message(
                {"type": "error", "message": "No command"}
            )
            return
        if command == "init":
            self.user_id = await self.login_as_new_user(
                json_message.get("nickname")
            )
        elif command == "login":
            self.user_id = await self.login(json_message)
        if not self.user_id:
            self.close(reason="Please login with the first message.")
            return

        # TODO: Handle commands

    async def on_close(self):
        print("WebSocket closed")

    async def data_received(self, chunk: bytes) -> None:
        pass

    async def login(self, json_message: dict[str, Any]) -> None | str:
        """Login the user."""
        user_id = json_message.get("user_id")
        auth_key = json_message.get("auth_key")

        if not (user_id and auth_key):
            await self.write_message(
                {"type": "error", "message": "No user_id or auth_key"}
            )
            return None

        user = await self.elasticsearch.get(
            index=self.elasticsearch_prefix + "-halt_mal_kurz-users",
            id=user_id,
        )

        if not user or not (user.get("user_id") == user_id):
            await self.write_message(
                {"type": "error", "message": "User not found"}
            )
            return None

        if user_id and PH.verify(user.get("auth_key_hash"), auth_key):
            # auth key verified
            if nickname := json_message.get("nickname"):
                if len(nickname) > 69:  # nice
                    nickname = nickname[:69]
                await self.elasticsearch.update(
                    index=self.elasticsearch_prefix + "-halt_mal_kurz-users",
                    id=user_id,
                    # TODO: read the fucking docs
                    body={"doc": {"nickname": nickname}},
                )
            else:
                nickname = user.get("nickname")

            await self.write_message(
                {
                    "type": "login",
                    "user_id": user_id,
                    "auth_key": auth_key,
                    "nickname": nickname,
                }
            )
            return user_id
        # login failed
        await self.write_message(
            {"type": "error", "message": "Wrong user_id or auth_key"}
        )
        return None

    @property
    def redis(self) -> Redis:
        """Return the Redis instance."""
        _r = self.settings.get("REDIS")
        if not _r:
            raise HTTPError(500)  # TODO: Better error handling
        return _r  # type: ignore

    @property
    def elasticsearch(self) -> None | AsyncElasticsearch:
        """Get the Elasticsearch client from the settings."""
        return self.settings.get("ELASTICSEARCH")

    @property
    def elasticsearch_prefix(self) -> str:
        """Get the Elasticsearch prefix from the settings."""
        return self.settings.get("ELASTICSEARCH_PREFIX", str())

    async def login_as_new_user(
        self, nickname: None | str = None
    ) -> str | None:
        """Login as a new user."""
        user_id = uuid.uuid4().hex
        auth_key = os.urandom(32).hex()
        nickname = nickname or generate_name(style="capital")
        if len(nickname) > 69:  # nice
            nickname = nickname[:69]
        await self.elasticsearch.index(
            index=self.elasticsearch_prefix + "-halt_mal_kurz-users",
            id=user_id,
            document={
                "user_id": user_id,
                "auth_key_hash": PH.hash(auth_key),
                "nickname": nickname,
            },
        )
        await self.write_message(
            {
                "type": "login",
                "user_id": user_id,
                "auth_key": auth_key,
                "nickname": nickname,
            }
        )
        return user_id

    async def player_is_owner_of_room(
        self, user_id: str, room_id: str
    ) -> bool:
        """Check if the user is the owner of the room."""
        return user_id == await self.redis.hget(
            self.get_redis_key("room", room_id, "settings"), "owner"
        )

    async def get_room_settings(self, room_id: str) -> dict[str, Any]:
        """Get the settings for a room."""
        return await self.redis.hgetall(  # type: ignore
            self.get_redis_key("room", room_id, "settings")
        )

    def get_redis_key(self, *args: str) -> str:
        """Get the redis key for "Nimm mal kurz!"."""
        prefix = self.settings.get("REDIS_PREFIX")
        if not args:
            return f"{prefix}:nimm-mal-kurz"
        return f"{prefix}:nimm-mal-kurz:{':'.join(args)}"

    async def is_in_room(self) -> None | str:
        """Check if the user is in a room the room ID."""
        user_id = self.user_id
        if not user_id:
            return None
        # get the room if from the user id with redis
        room_id = await self.redis.get(
            self.get_redis_key("user", user_id, "room")
        )
        if not room_id:
            return None
        if await self.redis.sismember(
            self.get_redis_key("room", room_id, "users"),
            user_id,
        ):
            return room_id
        return None
