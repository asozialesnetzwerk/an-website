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

from ..utils.utils import ModuleInfo
from .chat import (
    APIChatHandler,
    ChatWebSocketHandler,
    HTMLChatHandler,
    subscribe_to_redis_channel,
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
        required_background_tasks=(subscribe_to_redis_channel,),
    )
