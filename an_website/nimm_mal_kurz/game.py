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
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import orjson as json
import tornado.websocket as websocket
from aioredis import Redis
from argon2 import PasswordHasher
from elasticsearch import AsyncElasticsearch
from names_generator import generate_name
from tornado.web import HTTPError

PH = PasswordHasher()  # nicht die Webseite


class ValueType(Enum):
    """The type of value."""

    STRING = "String"


@dataclass(frozen=True)
class ArgumentInfo:
    """Information about an argument."""

    name: str
    description: str
    optional: bool
    default: Any
    value_type: ValueType = ValueType.STRING


@dataclass(frozen=True)
class CommandInfo:
    """Information about a command."""

    name: str
    description: str
    arguments: tuple[ArgumentInfo, ...]
    response: tuple[str, ...]  # all the response keys except of type
    response_types: tuple[str, ...]  # the values the "type" response can have


COMMANDS_IN_ROOM: dict[str, CommandInfo] = {
    "leave_room": CommandInfo(
        "leave_room",
        "Leave the current room.",
        tuple(),
        tuple(),
        ("error", "left_room"),
    ),
}

# commands that can only be used as the first command of the ws connection
LOGIN_COMMANDS: dict[str, CommandInfo] = {
    "init": CommandInfo(
        "init",
        "Initialize a new user.",
        (ArgumentInfo("name", "The name of the user.", optional=True),),
        ("user_id", "auth_key", "name"),
        ("error", "login"),
    ),
    "login": CommandInfo(
        "login",
        "Login as an existing user.",
        (
            ArgumentInfo("user_id", "The id of the user.", optional=False),
            ArgumentInfo(
                "auth_key", "The auth key of the user.", optional=False
            ),
            ArgumentInfo("name", "The name of the user.", optional=True),
        ),
        ("userid", "name"),
        ("error", "login"),
    ),
}


class GameWebsocket(websocket.WebSocketHandler):
    """The Websocket handler."""

    user_id: None | str = None

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
        command = command.lower()
        if command == "init":
            self.user_id = await self.login_as_new_user(
                json_message.get("name")
            )
        elif command == "login":
            self.user_id = await self.login(json_message)
        if not self.user_id:
            self.close(reason="Please log in with the first message.")
            return

        user_in_room = False
        room_id = await self.redis.get(
            self.get_redis_key("user", self.user_id, "room")
        )
        if room_id:
            if await self.redis.sismember(
                self.get_redis_key("room", room_id, "users"),
                self.user_id,
            ):
                user_in_room = True
            await self.handle_commands_in_room(room_id, command, json_message)

        if user_in_room:
            if command in COMMANDS_IN_ROOM:
                await self.handle_commands_in_room(
                    room_id, command, json_message
                )
            else:  # TODO: special case for when playing
                await self.write_message(
                    {"type": "error", "message": "Command not allowed in room"}
                )
            return

        if command == "create_room":
            await self.create_room()
        elif command == "join_room":
            await self.join_room()
        elif command == "list_public_rooms":
            await self.list_public_rooms()
        return

        # TODO: Handle commands

    async def handle_commands_in_room(
        self, room_id: str, command: str, json_msg: dict[str, Any]
    ) -> None:
        """Handle commands that are only allowed in a room."""
        if command == "leave_room":
            await self.leave_room(room_id)

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
            if name := json_message.get("name"):
                if len(name) > 69:  # nice
                    name = name[:69]
                await self.elasticsearch.update(
                    index=self.elasticsearch_prefix + "-halt_mal_kurz-users",
                    id=user_id,
                    # TODO: read the fucking docs
                    body={"doc": {"name": name}},
                )
            else:
                name = user.get("name")

            await self.write_message(
                {
                    "type": "login",
                    "user_id": user_id,
                    "name": name,
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

    async def login_as_new_user(self, name: None | str = None) -> str | None:
        """Login as a new user."""
        user_id = uuid.uuid4().hex
        auth_key = os.urandom(32).hex()
        name = name or generate_name(style="capital")
        if len(name) > 69:  # nice
            name = name[:69]
        await self.elasticsearch.index(
            index=self.elasticsearch_prefix + "-halt_mal_kurz-users",
            id=user_id,
            document={
                "user_id": user_id,
                "auth_key_hash": PH.hash(auth_key),
                "name": name,
            },
        )
        await self.write_message(
            {
                "type": "login",
                "user_id": user_id,
                "auth_key": auth_key,
                "name": name,
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

    async def create_room(self, json_msg: dict[str, Any]):
        """Create a new room."""
        # Create room with settings from the request
        room_id = str(uuid.uuid4())
        settings = {
            "name": self.get_argument("name", str()),
            "password": self.get_argument("password", str()),
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

    async def join_room(self):
        """Join a room."""
        if not self.get_room_id_specified_by_user():
            raise HTTPError(400, reason="No room ID provided.")
        # TODO: Check if user is already in a room
        # if None not in (self.get_room_id()):
        #     raise HTTPError(400, reason="User is currently in a room.")
        room_id = self.room_id or self.redis.get("user", self.user_id, "room")

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
            if _pw != self.get_argument("password", str()):
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

        await self.write_message(
            {
                "type": "joined_room",
                "room": {
                    "id": room_id,
                    "settings": await self.get_room_settings(room_id),
                },
            }
        )

    async def leave_room(self, room_id: str):
        """Leave the room."""
        users_redis_key = self.get_redis_key("room", room_id, "users")
        if not await self.redis.srem(
            users_redis_key,
            self.user_id,
        ):
            raise HTTPError(500, reason="Could not remove user from room.")
        await self.redis.delete(
            self.get_redis_key("user", self.user_id, "room")
        )
        # check if user is the last one in the room
        if not self.redis.smembers(users_redis_key):
            # TODO: improve room deletion
            await self.redis.delete(users_redis_key)
            await self.redis.delete(
                self.get_redis_key("room", room_id, "settings")
            )

        # TODO: Do stuff when game is running
        await self.write_message({"type": "left_room"})
