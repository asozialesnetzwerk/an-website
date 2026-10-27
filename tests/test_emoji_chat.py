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

"""Emoji chat."""

import asyncio
import json
import random
import socket
from urllib.parse import urlencode

import emoji
import pytest
from tornado.websocket import websocket_connect

from . import (
    REDIS_INFO,
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_json_response,
    fetch,
)

assert app and fetch  # type: ignore[truthy-bool]

KEYCAP = b"\xEF\xB8\x8F\xE2\x83\xA3".decode()


def number_to_emojis(n: int) -> str:
    """Convert a number to emoji(s)."""
    rest, n = divmod(n, 10)
    return f"{number_to_emojis(rest)}{n}{KEYCAP}" if rest else f"{n}{KEYCAP}"


async def test_emoji_chat_html_and_api(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test emoji chat."""
    if not REDIS_INFO:
        pytest.skip("no redis available")

    assert_valid_html_response(await fetch("/emoji-chat"), {200})

    response = assert_valid_html_response(
        await fetch(
            "/emoji-chat",
            method="POST",
            body=urlencode(
                {
                    "message": b"\xF0\x9F\x8F\xB3\xE2\x80\x8D\xE2\x9A\xA7".decode()
                }
            ),
        ),
        {200},
    )

    flag = b"\xF0\x9F\x8F\xB3\xEF\xB8\x8F\xE2\x80\x8D\xE2\x9A\xA7\xEF\xB8\x8F"

    assert flag in response.body

    data = assert_valid_json_response(await fetch("/api/emoji-chat"), {200})

    assert data["messages"][-1]["content"][0] == flag.decode()
    assert data["messages"][-1]["content"] == [flag.decode()]


async def test_emoji_chat_single_emoji_messages_api(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test emoji chat with single emojis."""
    if not REDIS_INFO:
        pytest.skip("no redis available")

    messages = []
    for i in range(10):
        message = number_to_emojis(i)
        messages.append(message)

        assert len(message) == 3, "is single emoji"

        data = assert_valid_json_response(
            await fetch(
                "/api/emoji-chat",
                method="POST",
                body=urlencode({"message": message}),
            ),
            {200},
        )

        assert data["messages"][-1]["content"] == [message]

        data = assert_valid_json_response(await fetch("/api/emoji-chat"), {200})

        assert data["messages"][-1]["content"] == [message]

    data = assert_valid_json_response(await fetch("/api/emoji-chat"), {200})
    for i in range(len(messages)):  # pylint: disable=consider-using-enumerate
        assert data["messages"][-len(messages) + i]["content"] == [messages[i]]


# pylint:disable-next=too-complex too-many-locals,too-many-branches,too-many-statements
async def test_emoji_chat_websocket(
    fetch: FetchCallable,  # noqa: F811
    http_server_port: tuple[socket.socket, int],
) -> None:
    """Test emoji chat websocket."""
    if not REDIS_INFO:
        pytest.skip("no redis available")

    ws_json_messages: list[str | bytes | None] = []

    r = random.Random()

    conn = await websocket_connect(
        f"ws://127.0.0.1:{http_server_port[1]}/websocket/emoji-chat",
        on_message_callback=ws_json_messages.append,
        ping_interval=1,
    )

    try:  # pylint: disable=too-many-try-statements
        own_message = "🏳️‍⚧️🏳️‍⚧️" + number_to_emojis(r.randrange(67, 674269))
        await conn.write_message(
            json.dumps({"type": "message", "message": own_message})
        )

        await asyncio.sleep(1)

        other_message = "🏳️‍⚧️🏳️‍⚧️🏳️‍⚧️" + number_to_emojis(
            r.randrange(67, 674269)
        )
        conn2 = await websocket_connect(
            f"ws://127.0.0.1:{http_server_port[1]}/websocket/emoji-chat",
            ping_interval=1,
        )
        try:
            init_msg_raw = await conn2.read_message()
            assert init_msg_raw
            init_msg = json.loads(init_msg_raw)
            assert init_msg["type"] == "init"
            other_user = init_msg["current_user"]
            await conn2.write_message(
                json.dumps({"type": "message", "message": other_message})
            )

            await asyncio.sleep(1)
        finally:
            conn2.close()

        authors: set[tuple[str, ...]] = set()
        sent_messages: list[str] = [own_message, other_message]

        for _ in range(10):
            msg = number_to_emojis(r.randrange(67, 67426942))
            data = assert_valid_json_response(
                await fetch(
                    "/api/emoji-chat",
                    method="POST",
                    body=urlencode({"message": msg}),
                ),
                {200},
            )
            authors.add(tuple(data["messages"][-1]["author"]))
            assert "".join(data["messages"][-1]["content"]) == msg
            sent_messages.append(msg)

        await asyncio.sleep(5)
        await conn.run()
    finally:
        conn.close()

    received_messages: list[str] = []

    current_user: list[str] | None = None

    last_timestamp = 0
    for message in ws_json_messages:
        assert message
        match json.loads(message):
            case {"type": "init", "current_user": list() as x}:
                current_user = x
            case {"type": "messages", "messages": list() as x}:
                pass  # ignore old messages
            case {
                "type": "message",
                "message": {
                    "author": list() as author,
                    "content": list() as content,
                    "timestamp": ts,
                },
            }:
                assert last_timestamp < ts
                last_timestamp = ts
                for e in author:
                    assert emoji.is_emoji(e), f"{e!r} needs to be emoji"
                for e in content:
                    assert emoji.is_emoji(e), f"{e!r} needs to be emoji"
                received_messages.append("".join(content))
                if "".join(content) == own_message:
                    assert author == current_user
                elif "".join(content) == other_message:
                    assert author == other_user
                else:
                    assert tuple(author) in authors
            case msg:
                raise AssertionError(f"unexpected message: {msg}")

    assert current_user
    assert (
        sent_messages == received_messages
    ), f"{sent_messages} == {received_messages}"
