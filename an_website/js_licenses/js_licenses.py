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
A page with a javascript web label page.

This is used for LibreJS to make sure the extension knows the licenses.
This isn't important, as the js files should contain the licenses themselves.
This script assumes that every file is licensed under AGPL v3.

See: https://www.gnu.org/software/librejs/free-your-javascript.html#step3
and https://www.gnu.org/licenses/javascript-labels.html
"""
from __future__ import annotations

import logging
import os.path

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import STATIC_DIR, ModuleInfo

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/js-lizenzen/", JsLicenses),),
        name="Javascript-Lizenzen",
        description="Informationen über die Lizenzen der Javascript-Dateien "
        "auf dieser Seite.",
        path="/js-lizenzen/",
        aliases=("/js-licenses/",),
        keywords=("Javascript", "License", "Lizenz"),
    )


def get_js_file_names():
    """Get the names of the js files in this project."""
    js_files_dir = os.path.join(STATIC_DIR, "js")
    return os.listdir(js_files_dir)


class JsLicenses(BaseRequestHandler):
    """The request handler for the js-licenses page."""

    async def get(self):
        """Handle the get requests to the js-licenses page."""
        await self.render(
            "pages/js_licenses.html", js_files=get_js_file_names()
        )
