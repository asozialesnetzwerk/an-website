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

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass

try:
    import urwid
except ImportError:
    print("Please install urwid with 'pip install urwid'.")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("Please install websockets with 'pip install websockets'.")
    sys.exit(1)


@dataclass
class LobbyState:
    """The currently available information."""

    user_id: str
    user_name: str
    auth_key: str
    rom_id: None | str


async def authenticate(
    websocket,
    name: None | str = None,
) -> None | LobbyState:
    """Authenticate with the server."""
    user_id = None
    auth_key = None
    cache_path = os.path.join(
        os.getenv("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
        "nimm-mal-kurz_curses-client/user_data.json",
    )
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="UTF-8") as f:
            _file_data = json.load(f)
            user_id = _file_data.get("id")
            auth_key = _file_data.get("key")

    if None in (user_id, auth_key):
        data = {"type": "init"}
        if name is not None:
            pass # TODO: ask user for name
    else:
        data = {
            "type": "login",
            "user_id": user_id,
            "auth_key": auth_key,
        }
    if name is not None:
        data["name"] = name
    await websocket.send(data)
    response = await websocket.recv()
    print(response)
    response_json = json.loads(response)
    if response_json["type"] == "login":
        if "auth_key" in response_json:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="UTF-8") as f:
                json.dump(
                    {
                        "id": response_json["user_id"],
                        "key": response_json["auth_key"],
                    },
                    f,
                    ensure_ascii=False,
                )
        return LobbyState(
            user_id=response_json["user_id"],
            user_name=response_json["name"],
            auth_key=response_json.get("auth_key") or auth_key,
            rom_id=None,
        )


def exit_on_q(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()


class TextInputBox(urwid.Filler):
    def __init__(
        self,
        body,
        valign=urwid.MIDDLE,
        height=urwid.PACK,
        min_height=None,
        top=0,
        bottom=0,
        on_input: Callable[[str], None | urwid.Widget] = lambda x: print(x),
    ):
        self.on_input = on_input
        super().__init__(body, valign, height, min_height, top, bottom)

    def keypress(self, size, key):
        if key != "enter":
            return super().keypress(size, key)
        _output = self.on_input(edit.edit_text)
        # sys.exit(type(_output))
        if _output is not None:
            self.original_widget = _output


def on_name_input(x: str) -> urwid.Text:
    """Handle input from the user."""
    asyncio.get_running_loop().create_task(
        authenticate(websocket, x)
    )


edit = urwid.Edit("What is your name?\n")
fill = TextInputBox(
    edit,
    on_input=lambda x: urwid.Text(
        f"Nice to meet you, {x}.\n\nPress Q to exit."
    ),
)
loop = urwid.MainLoop(fill, unhandled_input=exit_on_q)
loop.run()
