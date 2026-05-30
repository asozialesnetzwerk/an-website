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

from collections.abc import Iterable, Sequence
from typing import Final

from .. import STATIC_DIR


def get_themes() -> Iterable[str]:
    """Get a list of available themes."""
    for file in (STATIC_DIR / "css/themes").iterdir():
        if file.is_file() and file.name.endswith(".css"):
            yield file.name[:-4]
    yield "random"  # add random to the list of themes


THEMES: Final[Sequence[str]] = tuple(sorted(get_themes()))
NAMED_THEMES: Final[Sequence[tuple[str, str]]] = tuple(
    (theme, theme.replace("_", " ").title())
    for theme in THEMES
    if theme != "lowest_contrast"
)
RANDOM_THEMES: Final[Sequence[str]] = tuple(
    theme for theme, _ in NAMED_THEMES if theme not in {"random", "christmas"}
)
