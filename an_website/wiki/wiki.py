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

"""A redirect to an external wiki about the AN."""
from __future__ import annotations

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (
                r"/wiki",
                WikiHandler,
            ),
        ),
        name="Asoziales Wiki",
        description="Ein Wiki mit Sachen des Asozialen Netzwerkes",
        path="/wiki",
        keywords=(
            "Wiki",
            "asozial",
        ),
    )


class WikiHandler(HTMLRequestHandler):
    """The request handler for the wiki page."""

    def get(self, *, head: bool = False) -> None:
        """Handle the GET requests to the wiki page."""
        if head:
            return
        self.render(
            "pages/ask_for_redirect.html",
            redirect_url="https://wiki.asozial.org",
            from_url=None,
            discord=False,
        )
