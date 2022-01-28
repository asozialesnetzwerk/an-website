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

"""Minify all js files in this repo and move them to /static/js/."""
from __future__ import annotations

import os
import shutil
import sys

import rjsmin

DIR = os.path.dirname(__file__)

STATIC_DIR = os.path.join(DIR, "an_website/static/js")

if "--clean" in sys.argv:
    shutil.rmtree(STATIC_DIR)
os.makedirs(STATIC_DIR, exist_ok=True)

FILE_COUNTER, MINIFIED_COUNTER = 0, 0

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
        FILE_COUNTER += 1
        with open(os.path.join(folder, file), "r", encoding="UTF-8") as _f1:
            orig = _f1.read()
            small = (
                "// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8"
                + "270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0\n"
                + rjsmin.jsmin(orig)
                + "\n// @license-end\n"
            )
            new_file_path = os.path.join(STATIC_DIR, file)
            if os.path.isfile(new_file_path):
                with open(new_file_path, "r", encoding="UTF-8") as _f2_r:
                    if _f2_r.read() == small:
                        continue
            print(
                f"{file}: {len(orig)} -> {len(small)} chars "
                f"({(len(small) - len(orig)) / len(orig) * 100:.2f} %)"
            )
            MINIFIED_COUNTER += 1
            with open(new_file_path, "w", encoding="UTF-8") as _f2:
                _f2.write(small)
                _f2.flush()

print(f"Minified {MINIFIED_COUNTER} of {FILE_COUNTER} files.")
