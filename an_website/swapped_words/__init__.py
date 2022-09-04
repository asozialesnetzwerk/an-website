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

"""A page that swaps words."""

from __future__ import annotations

import os
from typing import Final

from .. import GH_ORG_URL
from ..utils.utils import ModuleInfo, PageInfo
from .swap import SwappedWords, SwappedWordsAPI

DIR: Final = os.path.dirname(__file__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/vertauschte-woerter", SwappedWords),
            (r"/api/vertauschte-woerter", SwappedWordsAPI),
        ),
        name="Vertauschte Wörter",
        description="Eine Seite, die Wörter vertauscht",
        path="/vertauschte-woerter",
        keywords=("vertauschte", "Wörter", "witzig", "Känguru"),
        sub_pages=(
            PageInfo(
                name="Plugin",
                description="Ein Browser-Plugin, welches Wörter vertauscht",
                path=f"{GH_ORG_URL}/VertauschteWoerterPlugin",
            ),
        ),
        aliases=(
            "/swapped-words",
            "/vertauschte-wörter",
            "/vertauschte-w%C3%B6rter",
        ),
    )
