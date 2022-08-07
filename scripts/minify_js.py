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

"""Minify all JS files in this repo and copy them to an_website/static/js."""

from __future__ import annotations

import os
import shutil
import sys

import rjsmin  # type: ignore[import]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.normpath(__file__)))

STATIC_DIR = os.path.join(REPO_ROOT, "an_website/static/js")
VENDORED_JS_DIR = os.path.join(REPO_ROOT, "an_website/static/vendored-js")


def get_license_str(file_content: str) -> None | str:
    """Get the license string of a JS file."""
    file_content = file_content.strip()
    if not (
        file_content.endswith("// @license-end")
        and file_content.startswith("// @license ")
    ):
        return None
    return file_content.split("\n")[0].removeprefix("// @license").strip()


def main() -> None | int | str:  # pylint: disable=useless-return  # noqa: D103
    """Find, copy and minify all JS files."""
    if "--clean" in sys.argv:
        shutil.rmtree(STATIC_DIR)
    os.makedirs(STATIC_DIR, exist_ok=True)

    file_counter, minified_counter = 0, 0

    for folder, _, files in os.walk(
        os.path.join(REPO_ROOT, "an_website"),
        topdown=True,
        onerror=None,
        followlinks=False,
    ):
        if folder in {STATIC_DIR, VENDORED_JS_DIR}:
            continue
        for file_name in files:
            if not file_name.endswith(".js"):
                continue
            file_counter += 1
            with open(
                os.path.join(folder, file_name), encoding="utf-8"
            ) as file:
                original = file.read()
            license_str = get_license_str(original)
            minified = rjsmin.jsmin(original)
            if license_str is None:
                print(f"\033[93m{file.name} has no license!\033[0m")
            else:
                minified = (
                    f"// @license {license_str}\n{minified}\n// @license-end\n"
                )
            new_file = os.path.join(STATIC_DIR, file_name)
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
