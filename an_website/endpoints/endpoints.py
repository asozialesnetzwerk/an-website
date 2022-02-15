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

from .. import ORJSON_OPTIONS
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, name_to_id


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/endpunkte/?", Endpoints),
            ("/api/endpoints/?", EndpointsAPI),
        ),
        name="API-Endpunkte",
        description="Alle API-Endpunkte unserer Webseite",
        path="/endpunkte",
        aliases=("/endpoints",),
        keywords=("API", "Endpoints", "Endpunkte"),
    )


class Endpoints(HTMLRequestHandler):
    """Endpoint page request handler."""

    async def get(self) -> None:
        """Handle a GET request."""
        return await self.render(
            "pages/endpoints.html",
            endpoints=self.get_endpoints(),
            name_to_id=name_to_id,
        )

    def get_endpoints(
        self,
    ) -> list[dict[str, str | list[dict[str, str | int | list[str]]]]]:
        """Get a list of all API endpoints and return it."""
        endpoints: list[
            dict[str, str | list[dict[str, str | int | list[str]]]]
        ] = []
        for _mi in self.settings["MODULE_INFOS"]:
            api_paths: list[dict[str, str | int | list[str]]] = [
                {
                    "path": _h[0],
                    "methods": ["OPTIONS", *_h[1].ALLOWED_METHODS],
                }
                for _h in _mi.handlers
                if _h[0].startswith("/api/")
                if self.is_authorized() or not _h[1].REQUIRES_AUTHORIZATION
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

    async def get(self) -> None:
        """Handle a GET request."""
        return await self.finish(
            json.dumps(self.get_endpoints(), option=ORJSON_OPTIONS)
        )
