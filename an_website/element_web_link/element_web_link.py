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

"""A redirect to the Matrix client."""
from __future__ import annotations

from tornado.web import RedirectHandler

from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/chat/*", RedirectHandler, {"url": "https://chat.asozial.org"}),
        ),
        name="Asozialer Chat",
        description="Matrix-Web-Client basierend auf Element",
        path="/chat",
        keywords=("Chat", "Matrix", "Element"),
        aliases=("/element",),
    )
