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

from typing import Union

import orjson as json

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/endpoints/", Endpoints),
            ("/api/endpoints/", EndpointsAPI),
        ),
        name="API-Endpunkte",
        description="Alle API-Endpunkte unserer Webseite",
        path="/endpoints/",
        keywords=("API", "Endpoints", "Endpunkte"),
    )


def get_endpoints() -> list[dict]:
    """Get a list of all API endpoints."""


class Endpoints(BaseRequestHandler):
    """Endpoint page request handler."""

    def get(self):
        """Handle a GET request."""
        self.render(
            "pages/endpoints.html",
            endpoints=self.get_endpoints(),
        )

    def get_endpoints(self) -> list[dict]:
        """Get a list of all API endpoints and return it."""
        endpoints: list[dict] = []
        for _mi in self.settings["MODULE_INFOS"]:
            api_paths: list[dict[str, Union[str, int, list]]] = [
                {
                    "path": _h[0],
                    "methods": ["OPTIONS", *_h[1].ALLOWED_METHODS],
                    "ratelimit-tokens": _h[1].RATELIMIT_TOKENS,
                }
                for _h in _mi.handlers
                if _h[0].startswith("/api/")
            ]
            if len(api_paths) > 0:
                endpoints.append(
                    {
                        "name": _mi.name,
                        "description": _mi.description,
                        "endpoints": api_paths,
                    }
                )
        return endpoints


class EndpointsAPI(Endpoints, APIRequestHandler):
    """Show a list of all API endpoints."""

    def get(self):
        """Handle a GET request."""
        self.finish(json.dumps(self.get_endpoints()))
