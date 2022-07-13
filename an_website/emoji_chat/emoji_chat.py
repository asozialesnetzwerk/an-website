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

"""A 😎 chat."""

from __future__ import annotations

from typing import Any

import emoji  # type: ignore
from redis.asyncio import Redis
from tornado.web import HTTPError

from ..utils.base_request_handler import BaseRequestHandler
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/emoji-chat", HTMLChatHandler),
            (r"/api/emoji-chat", APIChatHandler),
        ),
        name="Emoji-Chat",
        description="Ein 😎er Chat.",
        path="/emoji-chat",
        keywords=("Emoji Chat",),
        hidden=True,
    )


MAX_MESSAGE_SAVE_COUNT = 15
MAX_MESSAGE_LENGTH = 255
MAX_AUTHOR_LENGTH = 31

MESSAGES: list[str] = []


async def save_new_message(
    message: str,
    *,
    redis: None | Redis = None,  # type: ignore[type-arg]
    redis_prefix: None | str = None,
) -> None:
    """Save a new message."""
    MESSAGES.append(message)
    if len(MESSAGES) > MAX_MESSAGE_SAVE_COUNT:
        MESSAGES.pop(0)
    if redis is None:
        return
    await redis.set(f"{redis_prefix}:emoji-chat:messages", ",".join(MESSAGES))


def parse_messages(string: str) -> None:
    """Reset MESSAGES to the messages saved in the string."""
    MESSAGES.clear()
    MESSAGES.extend(spam.strip() for spam in string.split(","))


def check_only_emojis(string: str) -> bool:
    """Check whether a string only includes emojis."""
    is_emoji: list[bool] = [False] * len(string)

    def set_emojis(
        # pylint: disable=unused-argument
        emj: str,
        emj_data: dict[str, Any],
    ) -> None:
        for i in range(emj_data["match_start"], emj_data["match_end"]):
            is_emoji[i] = True

    emoji.demojize(string, language="en", version=-1, handle_version=set_emojis)

    return False not in is_emoji


class ChatHandler(BaseRequestHandler):
    """The request handler for the emoji chat."""

    async def get(
        # pylint: disable=unused-argument
        self,
        *,
        head: bool = False,
    ) -> None:
        """Show the users the current messages."""
        await self.render_chat(MESSAGES)

    async def post(self) -> None:
        """Let users send messages and show the users the current messages."""
        name = self.get_argument("name")
        message = self.get_argument("message")

        if not name:
            raise HTTPError(400, reason="Empty name not allowed.")
        if not name or not check_only_emojis(name):
            raise HTTPError(400, reason="Name needs to contain only emojis.")
        if len(name) > MAX_AUTHOR_LENGTH:
            raise HTTPError(
                400, reason=f"Name longer than {MAX_AUTHOR_LENGTH} chars."
            )

        if not message:
            raise HTTPError(400, reason="Empty message not allowed.")
        if not check_only_emojis(message.replace(" ", "")):
            raise HTTPError(
                400, reason="Message needs to contain only emojis or spaces."
            )
        if len(message) > MAX_MESSAGE_LENGTH:
            raise HTTPError(
                400, reason=f"Message longer than {MAX_MESSAGE_LENGTH} chars."
            )

        await save_new_message(
            f"{name}: {message}",
            redis=self.redis,
            redis_prefix=self.redis_prefix,
        )

        await self.render_chat(MESSAGES)

    async def render_chat(self, messages: list[str]) -> None:
        """Render the chat."""


class HTMLChatHandler(ChatHandler, HTMLRequestHandler):
    """The HTML request handler for the emoji chat."""

    async def render_chat(self, messages: list[str]) -> None:
        """Render the chat."""
        await self.render("pages/emoji_chat.html", messages=messages)


class APIChatHandler(ChatHandler, APIRequestHandler):
    """The API request handler for the emoji chat."""

    async def render_chat(self, messages: list[str]) -> None:
        """Render the chat."""
        await self.finish({"messages": messages})
