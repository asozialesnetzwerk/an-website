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

"""This script is used to create the hashes file for GitHub Pages."""

from __future__ import annotations

import sys
from pathlib import Path

from blake3 import blake3  # type: ignore

PATH = Path("an_website").absolute()


def hash_file(path: Path) -> str:
    """Hash a file with BLAKE3."""
    return str(blake3(path.read_bytes()).hexdigest())


def hash_files() -> str:
    """Hash all files."""
    return "\n".join(
        f"{hash_file(path)[:16]} {path.relative_to(PATH)}"
        for path in sorted(PATH.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    )


FILE_HASHES = hash_files()
HASH_OF_FILE_HASHES = blake3(FILE_HASHES.encode("utf-8")).hexdigest()


def main() -> None | int | str:  # pylint: disable=useless-return
    """Hash all files and write to stdout."""
    print("Hash der Datei-Hashes:")
    print(HASH_OF_FILE_HASHES)
    print()
    print("Datei-Hashes:")
    print(FILE_HASHES)

    return None


if __name__ == "__main__":
    sys.exit(main())
