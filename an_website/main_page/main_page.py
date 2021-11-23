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

"""The main page of the website."""
from __future__ import annotations

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        # the empty dict prevents the header from being changed
        handlers=((r"/", MainPage, {}), ("/index.html", MainPage, {})),
        name="Hauptseite",
        description="Die Hauptseite der Webseite",
        path="/",
        keywords=("asozial", "asoziales", "netzwerk"),
    )


class MainPage(BaseRequestHandler):
    """The request handler of the main page."""

    RATELIMIT_TOKENS = 0

    async def get(self):
        """Handle the GET requests and display the main page."""
        await self.render(
            "pages/main_page.html",
        )
