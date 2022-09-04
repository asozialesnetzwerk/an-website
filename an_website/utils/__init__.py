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

"""The utilities package with many helpful things used by other modules."""

from __future__ import annotations

import os
import sys
from typing import Final

from .request_handler import (
    ElasticRUM,
    ErrorPage,
    NotFoundHandler,
    ZeroDivision,
)
from .utils import ModuleInfo

DIR: Final = os.path.dirname(__file__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Utilities",
        description="Nützliche Werkzeuge für alle möglichen Sachen.",
        handlers=(
            (
                r"/error",
                ZeroDivision if sys.flags.dev_mode else NotFoundHandler,
                {},
            ),
            (r"/([1-5][0-9]{2}).html?", ErrorPage, {}),
            (
                r"/@elastic/apm-rum@(.+)/dist/bundles"
                r"/elastic-apm-rum.umd(\.min|).js(\.map|)",
                ElasticRUM,
            ),
        ),
        hidden=True,
    )
