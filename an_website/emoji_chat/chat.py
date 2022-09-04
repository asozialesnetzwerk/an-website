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

"""A 🆒 chat."""

from __future__ import annotations

import asyncio
import logging
import random
import sys
import time
from collections.abc import Awaitable
from typing import Any, Final, Literal

import orjson as json
from emoji import EMOJI_DATA, demojize, emoji_list, emojize
from redis.asyncio import Redis
from tornado.web import HTTPError
from tornado.websocket import WebSocketHandler

from .. import EPOCH_MS, EVENT_REDIS, ORJSON_OPTIONS
from ..utils.base_request_handler import BaseRequestHandler
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, Permission, ratelimit

LOGGER: Final = logging.getLogger(__name__)

EMOJIS: Final[tuple[str, ...]] = tuple(EMOJI_DATA)
EMOJIS_NO_FLAGS: Final[tuple[str, ...]] = tuple(
    emoji for emoji in EMOJIS if ord(emoji[0]) not in range(0x1F1E6, 0x1F200)
)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/emoji-chat", HTMLChatHandler),
            (r"/api/emoji-chat", APIChatHandler),
            (r"/websocket/emoji-chat", ChatWebSocketHandler),
        ),
        name="Emoji-Chat",
        description="Ein 🆒er Chat",
        path="/emoji-chat",
        keywords=("Emoji Chat",),
    )


MAX_MESSAGE_SAVE_COUNT = 100
MAX_MESSAGE_LENGTH = 20


def get_ms_timestamp() -> int:
    """Get the current time in ms."""
    return time.time_ns() // 1_000_000 - EPOCH_MS


async def save_new_message(
    author: str,
    message: str,
    redis: Redis[str],
    redis_prefix: str,
) -> None:
    """Save a new message."""
    message_dict = {
        "author": [data["emoji"] for data in emoji_list(author)],
        "content": [data["emoji"] for data in emoji_list(message)],
        "timestamp": get_ms_timestamp(),
    }
    await redis.rpush(
        f"{redis_prefix}:emoji-chat:message-list",
        json.dumps(message_dict, option=ORJSON_OPTIONS),
    )
    await redis.ltrim(
        f"{redis_prefix}:emoji-chat:message-list", -MAX_MESSAGE_SAVE_COUNT, -1
    )
    await asyncio.gather(
        *[
            conn.write_message(
                {
                    "type": "message",
                    "message": message_dict,
                }
            )
            for conn in OPEN_CONNECTIONS
        ]
    )


async def get_messages(
    redis: Redis[str],
    redis_prefix: str,
    start: int = -MAX_MESSAGE_SAVE_COUNT,
    stop: int = -1,
) -> list[dict[str, Any]]:
    """Get the messages."""
    messages = await redis.lrange(
        f"{redis_prefix}:emoji-chat:message-list", start, stop
    )
    return [json.loads(message) for message in messages]


def check_message_invalid(message: str) -> Literal[False] | str:
    """Check if a message is an invalid message."""
    if not message:
        return "Empty message not allowed."

    if not check_only_emojis(message):
        return "Message can only contain emojis."

    if len(emoji_list(message)) > MAX_MESSAGE_LENGTH:
        return f"Message longer than {MAX_MESSAGE_LENGTH} emojis."

    return False


def check_only_emojis(string: str) -> bool:
    """Check whether a string only includes emojis."""
    is_emoji: list[bool] = [False] * len(string)

    def set_emojis(emoji: str, emoji_data: dict[str, Any]) -> str:
        # pylint: disable=unused-argument
        for i in range(emoji_data["match_start"], emoji_data["match_end"]):
            is_emoji[i] = True
        return ""

    demojize(string, language="en", version=-1, handle_version=set_emojis)

    return False not in is_emoji


def emojize_user_input(string: str) -> str:
    """Emojize user input."""
    string = emojize(string, language="de")
    string = emojize(string, language="en")
    string = emojize(string, language="alias")
    return string


def normalize_emojis(string: str) -> str:
    """Normalize emojis in a string."""
    return emojize(demojize(string))


def get_random_name() -> str:
    """Generate a random name."""
    return normalize_emojis(
        "".join(random.sample(EMOJIS_NO_FLAGS, 5))  # nosec: B311
    )


class ChatHandler(BaseRequestHandler):
    """The request handler for the emoji chat."""

    RATELIMIT_GET_BUCKET = "emoji-chat-get-messages"
    RATELIMIT_GET_LIMIT = 10
    RATELIMIT_GET_COUNT_PER_PERIOD = 10
    RATELIMIT_GET_PERIOD = 1

    RATELIMIT_POST_BUCKET = "emoji-chat-send-message"
    RATELIMIT_POST_LIMIT = 5
    RATELIMIT_POST_COUNT_PER_PERIOD = 5
    RATELIMIT_POST_PERIOD = 5

    async def get(
        self,
        *,
        head: bool = False,
    ) -> None:
        """Show the users the current messages."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        if head:
            return

        await self.render_chat(
            await get_messages(self.redis, self.redis_prefix)
        )

    async def get_name(self) -> str:
        """Get the name of the user."""
        cookie = self.get_secure_cookie(
            "emoji-chat-name",
            max_age_days=90,
            min_version=2,
        )

        name = cookie.decode("UTF-8") if cookie else get_random_name()

        # save it in cookie or reset expiry date
        if not self.get_secure_cookie(
            "emoji-chat-name", max_age_days=30, min_version=2
        ):
            self.set_secure_cookie(
                "emoji-chat-name",
                name.encode("UTF-8"),
                expires_days=90,
                path="/",
                samesite="Strict",
            )

        geoip = await self.geoip() or {}
        if "country_flag" in geoip:
            flag = geoip["country_flag"]
        elif self.request.host_name.endswith(".onion"):
            flag = "🏴☠"
        else:
            flag = "❔"

        return normalize_emojis(name + flag)

    async def get_name_as_list(self) -> list[str]:
        """Return the name as list of emojis."""
        return [emoji["emoji"] for emoji in emoji_list(await self.get_name())]

    async def post(self) -> None:
        """Let users send messages and show the users the current messages."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        message = emojize_user_input(
            normalize_emojis(self.get_argument("message"))
        )

        if err := check_message_invalid(message):
            raise HTTPError(400, reason=err)

        await save_new_message(
            await self.get_name(),
            message,
            redis=self.redis,
            redis_prefix=self.redis_prefix,
        )

        await self.render_chat(
            await get_messages(self.redis, self.redis_prefix)
        )

    async def render_chat(self, messages: list[dict[str, Any]]) -> None:
        """Render the chat."""
        raise NotImplementedError


class HTMLChatHandler(ChatHandler, HTMLRequestHandler):
    """The HTML request handler for the emoji chat."""

    async def render_chat(self, messages: list[dict[str, Any]]) -> None:
        """Render the chat."""
        await self.render(
            "pages/emoji_chat.html",
            messages=messages,
            user_name=await self.get_name_as_list(),
        )


class APIChatHandler(ChatHandler, APIRequestHandler):
    """The API request handler for the emoji chat."""

    async def render_chat(self, messages: list[dict[str, Any]]) -> None:
        """Render the chat."""
        await self.finish(
            {
                "current_user": await self.get_name_as_list(),
                "messages": messages,
            }
        )


OPEN_CONNECTIONS: list[ChatWebSocketHandler] = []


class ChatWebSocketHandler(WebSocketHandler, ChatHandler):
    """The handler for the chat WebSocket."""

    name: str
    connection_time: int

    def on_close(self) -> None:  # noqa: D102
        LOGGER.info("WebSocket closed")
        OPEN_CONNECTIONS.remove(self)
        for conn in OPEN_CONNECTIONS:
            conn.send_users()

    def on_message(self, _msg: str | bytes) -> Awaitable[None] | None:
        """Respond to an incoming message."""
        if not _msg:
            return None
        message: dict[str, Any] = json.loads(_msg)
        if message["type"] == "message":
            if "message" not in message:
                return self.write_message(
                    {
                        "type": "error",
                        "error": "Message needs message key with the message.",
                    }
                )
            return self.save_new_message(message["message"])

        return self.write_message(
            {"type": "error", "error": f"Unknown type {message['type']}."}
        )

    def open(self, *args: str, **kwargs: str) -> Awaitable[None] | None:
        """Handle an opened connection."""
        LOGGER.info("WebSocket opened")
        self.write_message(
            {
                "type": "init",
                "current_user": [
                    emoji["emoji"] for emoji in emoji_list(self.name)
                ],
            }
        )

        self.connection_time = get_ms_timestamp()
        OPEN_CONNECTIONS.append(self)
        for conn in OPEN_CONNECTIONS:
            conn.send_users()

        return self.send_messages()

    async def prepare(self) -> None:  # noqa: D102
        self.now = await self.get_time()

        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        self.name = await self.get_name()

        if not await self.ratelimit(True):
            await self.ratelimit()

    async def render_chat(self, messages: list[dict[str, Any]]) -> None:
        """Render the chat."""
        raise NotImplementedError

    async def save_new_message(self, msg_text: str) -> None:
        """Save a new message."""
        msg_text = emojize_user_input(normalize_emojis(msg_text).strip())
        if err := check_message_invalid(msg_text):
            return await self.write_message({"type": "error", "error": err})

        if self.settings.get("RATELIMITS") and not self.is_authorized(
            Permission.RATELIMITS
        ):
            if not EVENT_REDIS.is_set():
                return await self.write_message({"type": "ratelimit"})

            ratelimited, headers = await ratelimit(
                self.redis,
                self.redis_prefix,
                str(self.request.remote_ip),
                bucket=self.RATELIMIT_POST_BUCKET,
                max_burst=self.RATELIMIT_POST_LIMIT - 1,
                count_per_period=self.RATELIMIT_POST_COUNT_PER_PERIOD,
                period=self.RATELIMIT_POST_PERIOD,
                tokens=1,
            )

            if ratelimited:
                return await self.write_message(
                    {"type": "ratelimit", **headers}
                )

        return await save_new_message(
            self.name, msg_text, self.redis, self.redis_prefix
        )

    async def send_messages(self) -> None:
        """Send this WebSocket all current messages."""
        return await self.write_message(
            {
                "type": "messages",
                "messages": await get_messages(self.redis, self.redis_prefix),
            },
        )

    def send_users(self) -> None:
        """Send this WebSocket all current users."""
        if sys.flags.dev_mode:
            self.write_message(
                {
                    "type": "users",
                    "users": [
                        {
                            "name": conn.name,
                            "joined_at": conn.connection_time,
                        }
                        for conn in OPEN_CONNECTIONS
                    ],
                }
            )
