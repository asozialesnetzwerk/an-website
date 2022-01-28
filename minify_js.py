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

import rjsmin

DIR = os.path.dirname(__file__)

STATIC_DIR = os.path.join(DIR, "an_website/static/js")

os.makedirs(STATIC_DIR, exist_ok=True)

for folder, _, files in os.walk(
    os.path.join(DIR, "an_website"),
    topdown=True,
    onerror=None,
    followlinks=False,
):
    if folder != STATIC_DIR:
        for file in files:
            if file.endswith(".js"):
                with open(
                    os.path.join(folder, file), "r", encoding="UTF-8"
                ) as _f1:
                    content = rjsmin.jsmin(_f1.read())
                    with open(
                        os.path.join(STATIC_DIR, file), "w", encoding="UTF-8"
                    ) as _f2:
                        _f2.write(
                            "// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8"
                            + "270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-3.0\n"
                            + content
                            + "\n// @license-end\n"
                        )
                        _f2.flush()
