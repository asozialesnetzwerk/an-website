#!/bin/env python3
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

"""Minify all JS files in this repo and move them to /static/js."""
from __future__ import annotations

import os
import shutil
import sys

import rjsmin

DIR = os.path.dirname(__file__)

STATIC_DIR = os.path.join(DIR, "an_website/static/js")


def main() -> None:
    if "--clean" in sys.argv:
        shutil.rmtree(STATIC_DIR)
    os.makedirs(STATIC_DIR, exist_ok=True)

    file_counter, minified_counter = 0, 0

    for folder, _, files in os.walk(
        os.path.join(DIR, "an_website"),
        topdown=True,
        onerror=None,
        followlinks=False,
    ):
        if folder == STATIC_DIR:
            continue
        for file in files:
            if not file.endswith(".js"):
                continue
            file_counter += 1
            with open(os.path.join(folder, file), encoding="UTF-8") as f:
                original = f.read()
            minified = (
                "// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8"
                + "270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0\n"
                + rjsmin.jsmin(original)
                + "\n// @license-end\n"
            )
            new_file = os.path.join(STATIC_DIR, file)
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


if __name__ == "__main__":
    main()
