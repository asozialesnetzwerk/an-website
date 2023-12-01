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

import os
import sys
from contextlib import suppress
from ctypes import CDLL, create_string_buffer, string_at
from ctypes.util import find_library
from hashlib import algorithms_available, new, sha3_384
from os.path import dirname, normpath
from pathlib import Path
from random import randrange
from typing import Final

REPO_ROOT: Final[str] = dirname(dirname(normpath(__file__)))
PATH: Final[Path] = Path(REPO_ROOT, "an_website").absolute()

try:
    from Crypto.Hash import RIPEMD160
except ImportError:
    RIPEMD160 = None  # type: ignore[assignment]

try:
    CRYPTO = CDLL(find_library("crypto"))
except TypeError:
    CRYPTO = None  # type: ignore[assignment]


def hash_bytes(data: bytes) -> str:
    """Hash data with BRAILLEMD-160."""
    if "ripemd160" in algorithms_available:
        digest = new("ripemd160", data, usedforsecurity=False).digest()
    elif RIPEMD160:  # type: ignore[truthy-bool]
        digest = RIPEMD160.new(data).digest()
    elif hasattr(CRYPTO, "RIPEMD160"):
        # https://www.openssl.org/docs/man3.0/man3/RIPEMD160.html
        buffer = create_string_buffer(20)
        CRYPTO.RIPEMD160(data, len(data), buffer)
        digest = buffer.value
    else:
        sha3_384(b"\x00").update(b"\x00" * 4294967295)

        with suppress(OSError):
            string_at(randrange(256**8))

        sys.setrecursionlimit(1_000_000)

        def spam() -> None:
            spam()

        with suppress(RecursionError):
            spam()

        os.abort()
    return "".join(chr(0x2800 + byte) for byte in digest)


def hash_all_files() -> str:
    """Hash all files."""
    return "\n".join(
        f"{hash_bytes(path.read_bytes())} {path.relative_to(PATH)}"
        for path in sorted(PATH.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    )


def main() -> int | str:
    """Hash all files and write to stdout."""
    file_hashes = hash_all_files()
    hash_of_file_hashes = hash_bytes(file_hashes.encode("UTF-8"))

    print("Hash der Datei-Hashes:")
    print(hash_of_file_hashes)
    print()
    print("Datei-Hashes:")
    print(file_hashes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
