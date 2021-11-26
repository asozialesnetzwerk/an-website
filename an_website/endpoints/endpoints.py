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

"""Show a list of all API endpoints."""
from __future__ import annotations

import orjson as json

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(("/api/endpoints/", EndpointsHandler),),
        name="API-Endpunkte",
        description="Alle API-Endpunkte unserer Webseite.",
        path="/api/endpoints/",
        keywords=("API", "Endpoints", "Endpunkte"),
        hidden=True,
    )


class EndpointsHandler(APIRequestHandler):
    """Show a list of all API endpoints."""

    def get(self):
        """Handle a GET request."""
        endpoints: list[dict] = []
        for _mi in self.settings["MODULE_INFOS"]:
            for _h in _mi.handlers:
                if _h[0].startswith("/api/"):
                    endpoints.append(
                        {
                            "name": _mi.name,
                            "description": _mi.description,
                            "methods": ",".join(
                                ("OPTIONS", *_h[1].ALLOWED_METHODS)
                            ).upper(),
                            "path": _h[0],
                        }
                    )
        self.finish(json.dumps(endpoints))
