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

"""Minify all CSS files in style and move them to an_website/static/style."""
from __future__ import annotations

import os
import shutil
import sys

import rcssmin  # type: ignore[import]

DIR = os.path.dirname(__file__)

STATIC_DIR = os.path.join(DIR, "an_website/static/style")
STYLE_DIR = os.path.join(DIR, "style")


def main() -> None | int | str:  # pylint: disable=useless-return  # noqa: D103
    if "--clean" in sys.argv:
        shutil.rmtree(STATIC_DIR)
    os.makedirs(STATIC_DIR, exist_ok=True)

    file_counter, minified_counter = 0, 0

    for folder, _, files in os.walk(
        STYLE_DIR,
        topdown=True,
        onerror=None,
        followlinks=False,
    ):
        new_dir = (
            os.path.join(
                STATIC_DIR, folder[len(STYLE_DIR + "/") :]  # noqa: E203
            )
            if folder.startswith(STYLE_DIR + "/")
            else STATIC_DIR
        )
        os.makedirs(new_dir, exist_ok=True)
        for file in files:
            if not file.endswith(".css"):
                continue
            file_counter += 1
            with open(os.path.join(folder, file), encoding="UTF-8") as f:
                original = f.read()
            minified = rcssmin.cssmin(original) + "\n"
            new_file = os.path.join(new_dir, file)
            if os.path.isfile(new_file):
                with open(new_file, encoding="UTF-8") as f:
                    if f.read() == minified:
                        continue
            print(
                f"{file}: {len(original)} -> {len(minified)} characters "
                f"({(len(minified) - len(original)) / len(original) * 100:.2f} %)"
            )
            minified_counter += 1
            with open(new_file, "w", encoding="UTF-8") as f:
                f.write(minified)
                f.flush()

    print(f"Minified {minified_counter} of {file_counter} files.")

    return None


if __name__ == "__main__":
    sys.exit(main())
