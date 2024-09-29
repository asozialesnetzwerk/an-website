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

"""A module providing THEMES."""

from __future__ import annotations

from typing import Final

from .. import STATIC_DIR


def get_themes() -> tuple[str, ...]:
    """Get a list of available themes."""
    files = (STATIC_DIR / "css/themes").iterdir()
    return (
        *(file.name[:-4] for file in files if file.name.endswith(".css")),
        "random",  # add random to the list of themes
        "random_dark",
    )


THEMES: Final[tuple[str, ...]] = get_themes()
