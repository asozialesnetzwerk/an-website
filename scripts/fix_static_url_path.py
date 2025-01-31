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

"""Fix static URL paths."""

from __future__ import annotations

import os
import sys
import typing
from collections.abc import Iterable
from pathlib import Path
from typing import Final, NamedTuple, TextIO

REPO_ROOT: Final[Path] = Path(__file__).absolute().parent.parent
FIX_STATIC_FILE_SOURCE: Final = (
    REPO_ROOT / "an_website/utils/fix_static_path_impl.py"
)
# Same as in ../tests/__init__.py
ERROR_QUERY: Final[str] = "XXX-COULD-NOT-ADD-HASH-XXX"


class FixResult(NamedTuple):
    """Result of fixing a static URL path."""

    success: bool
    string: str


def fix_static_url_path(path: str, /) -> FixResult:
    """Fix static URL path."""
    if not path.startswith("/static"):
        return FixResult(False, "not a static url path")
    if path.endswith("/"):
        return FixResult(False, "ends with /")
    if "?" in path:
        return FixResult(False, "already contains query")

    objects: dict[str, typing.Any] = {
        "STATIC_DIR": REPO_ROOT / "an_website/static"
    }
    exec(FIX_STATIC_FILE_SOURCE.read_text("UTF-8"), objects)

    create_file_hashes_dict = objects["create_file_hashes_dict"]
    fix_static_path_impl = objects["fix_static_path_impl"]

    file_hashes = create_file_hashes_dict(path.removeprefix("/static/").__eq__)
    if (fixed_path := fix_static_path_impl(path, file_hashes)) == path:
        fixed_path = f"{path}?{ERROR_QUERY}"
    return FixResult(True, fixed_path)


def main(args: Iterable[str], /) -> int:
    """Fix static URL paths."""
    err_count = 0
    success_count = 0

    for arg in args:
        file: TextIO
        text: str
        result = fix_static_url_path(arg)
        if result.success:
            file = sys.stdout
            text = result.string
            success_count += 1
        else:
            file = sys.stderr
            text = f"failed to fix {arg}: {result.string}"
            err_count += 1
        print(text, file=file)

    if not success_count and not err_count:
        print("Provide static URL paths as arguments", file=sys.stderr)
        return os.EX_USAGE

    return min(err_count, max(1, os.EX_USAGE - 1))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
