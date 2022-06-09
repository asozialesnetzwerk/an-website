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
from hashlib import blake2b
from pathlib import Path

PATH = Path("an_website").absolute()


def hash_bytes(data: bytes) -> str:
    """Hash data with fast BLAKE2bRAILLE20."""
    return "".join(
        chr(spam + 0x2800) for spam in blake2b(data, digest_size=20).digest()
    )


def hash_all_files() -> str:
    """Hash all files."""
    return "\n".join(
        f"{hash_bytes(path.read_bytes())} {path.relative_to(PATH)}"
        for path in sorted(PATH.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    )


FILE_HASHES = hash_all_files()
HASH_OF_FILE_HASHES = hash_bytes(FILE_HASHES.encode("utf-8"))


def main() -> None | int | str:  # pylint: disable=useless-return
    """Hash all files and write to stdout."""
    print("Hash der Datei-Hashes:")
    print(HASH_OF_FILE_HASHES)
    print()
    print("Datei-Hashes:")
    print(FILE_HASHES)

    return None


def benchmark() -> None | int | str:  # pylint: disable=useless-return
    """Benchmark the hashing of all files."""
    from timeit import timeit  # pylint: disable=import-outside-toplevel

    count = 10
    result = timeit(
        lambda: hash_bytes(hash_all_files().encode("utf-8")),
        number=count,
    )
    print(f"{result=}, {result/count=}")
    return None


if __name__ == "__main__":
    sys.exit(benchmark() if "--benchmark" in sys.argv else main())
