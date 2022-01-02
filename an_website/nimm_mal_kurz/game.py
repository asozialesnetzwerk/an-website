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
from typing import Any

import orjson as json
import tornado.websocket as websocket
from aioredis import Redis
from argon2 import PasswordHasher
from elasticsearch import AsyncElasticsearch
from names_generator import generate_name
from tornado.web import HTTPError

from ..utils.utils import ModuleInfo, str_to_bool

PH = PasswordHasher()  # nicht die Webseite


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            # (r"/api/nimm-mal-kurz/raum/([a-z0-9]+)/", NimmMalKurzRoomAPI),
            (r"/nimm-mal-kurz/spielen/", GameWebsocket),
        ),
        name="Nimm mal kurz!",
        description='Ein Klon des beliebten Karten-Spiels "Halt mal kurz!".',
        keywords=(
            "Halt mal kurz",
            "Nimm mal kurz",
            "Kartenspiel",
        ),
    )


@dataclass(frozen=True)
class ArgumentInfo:
    """Information about an argument."""

    name: str
    description: str
    optional: bool
    default: None | Any = None
    type: type = str


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

GENERAL_COMMANDS: dict[str, CommandInfo] = {
    "create_room": CommandInfo(
        "create_room",
        "Create a new room.",
        (
            ArgumentInfo("name", "The name of the room.", optional=False),
            ArgumentInfo(
                "password",
                "The password of the room.",
                optional=True,
                default="",
            ),
            ArgumentInfo(
                "public",
                "Whether the room is public or not.",
                optional=True,
                default=False,
                type=bool,
            ),
            ArgumentInfo(
                "max_players",
                "The max players of the room.",
                optional=True,
                default=5,
                type=int,
            ),
            ArgumentInfo(
                "card_count",
                "The card count of the room.",
                optional=True,
                default=5,
                type=int,
            ),
            ArgumentInfo(
                "max_time_per_card",
                "The max time per card of the room.",
                optional=True,
                default=60,  # in seconds
                type=int,
            ),
        ),
        ("room_id", "name", "password"),
        ("error", "room_join"),
    ),
}

REDIS_EXP = 60 * 60 * 24 * 7  # 7 days


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
        # user is not in a room
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
            "name": json_msg.get("name", str()),
            "password": json_msg.get("password", str()),
            "public": str_to_bool(json_msg.get("public", "false"), False),
            "max_players": int(json_msg.get("max_players", 5)),
            "card_count": int(json_msg.get("card_count", 5)),
            "max_time_per_card": int(
                json_msg.get("max_time_per_card", "30")  # in seconds
            ),
            "owner": self.user_id,
        }
        await self.redis.hset(
            self.get_redis_key("room", room_id, "settings"), mapping=settings
        )
        await self.redis.expire(
            self.get_redis_key("room", room_id, "settings"), REDIS_EXP
        )
        # Add the room to the user's list of rooms
        await self.redis.sadd(
            self.get_redis_key("room", room_id, "users"), self.user_id
        )
        await self.redis.expire(
            self.get_redis_key("room", room_id, "users"), REDIS_EXP
        )

        if settings["public"]:
            await self.redis.sadd(self.get_redis_key("public-rooms"), room_id)

        await self.write_message(
            {
                "type": "room_join",
                "room": {
                    "id": room_id,
                    "settings": settings,
                },
            }
        )

    async def join_room(self, json_msg: dict[str, Any]) -> None:
        """Join a room."""
        if "room_id" not in json_msg:
            await self.write_message(
                {"type": "error", "message": "No room_id"}
            )
            return
        room_id = json_msg["room_id"]

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
            await self.write_message(
                {"type": "error", "message": "Room is full."}
            )
            return

        if (
            _pw := self.redis.hget(  # pw check
                self.get_redis_key("room", room_id, "settings"), "password"
            )
        ) and _pw != json_msg.get("password", str()):
            await self.write_message(
                {"type": "error", "message": "Wrong password."}
            )
            return

        await self.redis.sadd(
            self.get_redis_key("room", room_id, "users"),
            self.user_id,
        )
        await self.redis.set(
            self.get_redis_key("user", self.user_id, "room"),
            room_id,
        )

        await self.write_message(
            {
                "type": "room_join",
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
            await self.delete_room(room_id)

        # TODO: Do stuff when game is running
        await self.write_message({"type": "left_room"})

    async def delete_room(self, room_id: str):
        """Delete a room."""
        await self.redis.delete(self.get_redis_key("room", room_id, "users"))
        await self.redis.delete(
            self.get_redis_key("room", room_id, "settings")
        )
        await self.redis.srem(self.get_redis_key("public-rooms"), room_id)
