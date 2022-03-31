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

"""A page with the kangaroo comics by Zeit Online."""

from __future__ import annotations

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/kaenguru-comics", KangarooComics),),
        name="Känguru-Comics",
        description=(
            "Känguru-Comics von Zeit Online, Marc-Uwe Kling und Bernd Kissel"
        ),
        path="/kaenguru-comics",
        keywords=("Känguru", "Comics", "Zeit", "Marc-Uwe Kling"),
        aliases=(
            "/kangaroo-comics",
            "/comics",
            "/känguru-comics",
            "/k%C3%A4nguru-comics",
        ),
    )


class KangarooComics(HTMLRequestHandler):
    """Request handler for the kangaroo comics page."""

    def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the kangaroo comics page."""
        if head:
            return
        self.render("pages/kangaroo_comics.html")
