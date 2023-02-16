#!/usr/bin/env python3

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

"""Fix the word-files used for hangman_solver."""

from __future__ import annotations

import sys
from pathlib import Path


def fix_word_files() -> int | str:
    """Fix the word-files."""
    folder = (
        Path(__file__).parent.parent / "an_website" / "hangman_solver" / "words"
    )

    for file in folder.rglob("*.txt"):
        text = file.read_text(encoding="CP1252")
        lines = text.strip().split("\n")
        new_text = "\n".join(sorted(frozenset(map(str.lower, lines)))) + "\n"
        if text == new_text:
            continue
        print(f"Fixing {file}", file=sys.stderr)
        file.write_text(new_text, encoding="CP1252")

    return 0


if __name__ == "__main__":
    fix_word_files()
