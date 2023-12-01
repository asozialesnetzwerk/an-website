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

"""
A page with all the JavaScript files and their licenses.

This is used for LibreJS to make sure the extension knows the licenses.
This isn't important, as the JS files should contain the licenses themselves.

See: https://www.gnu.org/software/librejs/free-your-javascript.html#step3
and https://www.gnu.org/licenses/javascript-labels.html
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from functools import cache
from pathlib import Path
from typing import Final

from .. import STATIC_DIR
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo

LOGGER: Final = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/js-lizenzen", JSLicenses),),
        name="JavaScript-Lizenzen",
        description=(
            "Informationen über die Lizenzen der JavaScript-Dateien "
            "auf dieser Seite"
        ),
        path="/js-lizenzen",
        aliases=("/js-licenses",),
        keywords=("JavaScript", "License", "Lizenz"),
    )


LICENSES: Final[Mapping[str, str]] = {
    "magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt": (
        "https://www.gnu.org/licenses/agpl-3.0.html"
    ),
    "magnet:?xt=urn:btih:d3d9a9a6595521f9666a5e94cc830dab83b65699&dn=expat.txt": (
        "https://www.jclark.com/xml/copying.txt"
    ),
}


@cache
def get_js_filenames_and_licenses() -> list[tuple[str, str, str]]:
    """
    Get the names of the JS files in this project.

    Returns a list of tuples with filename, license and license URL.
    """
    js_files_dir = os.path.join(STATIC_DIR, "js")
    licenses_list: list[tuple[str, str, str]] = []
    for path in Path(js_files_dir).rglob("*.js"):
        if not path.is_file():
            continue
        filename = str(path.relative_to(js_files_dir))
        with path.open(encoding="UTF-8") as file:
            license_line = file.readline().strip().removeprefix('"use strict";')
        if not license_line.startswith("// @license "):
            LOGGER.warning("%s has no license comment", filename)
            # TODO: exit in dev mode if this fails
            continue
        magnet, name = (
            license_line.removeprefix("// @license").strip().split(" ")
        )
        licenses_list.append((filename, name.strip(), LICENSES[magnet.strip()]))
    return licenses_list


class JSLicenses(HTMLRequestHandler):
    """The request handler for the JS licenses page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the JS licenses page."""
        if head:
            return
        await self.render(
            "pages/js_licenses.html", js_files=get_js_filenames_and_licenses()
        )
