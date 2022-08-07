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

"""Minify all CSS files in style and copy them to an_website/static/style."""

from __future__ import annotations

import os
import shutil
import sys

import rcssmin  # type: ignore[import]

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

STATIC_DIR = os.path.join(REPO_ROOT, "an_website/static/style")
STYLE_DIR = os.path.join(REPO_ROOT, "style")


def main() -> None | int | str:  # pylint: disable=useless-return  # noqa: D103
    """Copy and minify all CSS files."""
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
        for file_name in files:
            if not file_name.endswith(".css"):
                continue
            file_counter += 1
            with open(
                os.path.join(folder, file_name), encoding="utf-8"
            ) as file:
                original = file.read()
            minified = rcssmin.cssmin(original, keep_bang_comments=True) + "\n"
            new_file = os.path.join(new_dir, file_name)
            if os.path.isfile(new_file):
                with open(new_file, encoding="utf-8") as file:
                    if file.read() == minified:
                        continue
            print(
                f"{file.name.removeprefix(f'{REPO_ROOT}/')}: "
                f"{len(original)} -> {len(minified)} characters "
                f"({(len(minified) - len(original)) / len(original) * 100:.2f} %)"
            )
            minified_counter += 1
            with open(new_file, "w", encoding="utf-8") as file:
                file.write(minified)

    print(f"Minified {minified_counter} of {file_counter} files.")

    return None


if __name__ == "__main__":
    sys.exit(main())
