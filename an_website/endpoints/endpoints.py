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

from typing import ClassVar

import orjson as json
from tornado.web import RedirectHandler

from .. import ORJSON_OPTIONS
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, name_to_id


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/endpunkte", Endpoints),
            ("/api/endpunkte", EndpointsAPI),
            ("/api/endpoints/*", RedirectHandler, {"url": "/api/endpunkte"}),
        ),
        name="API-Endpunkte",
        description="Alle API-Endpunkte unserer Webseite",
        path="/endpunkte",
        aliases=("/endpoints",),
        keywords=("API", "Endpoints", "Endpunkte"),
    )


class Endpoints(HTMLRequestHandler):
    """Endpoint page request handler."""

    async def get(self, *, head: bool = False) -> None:
        """Handle a GET request."""
        if head:
            return
        return await self.render(
            "pages/endpoints.html",
            endpoints=self.get_endpoints(),
            name_to_id=name_to_id,
        )

    def get_endpoints(
        self,
    ) -> list[dict[str, str | list[dict[str, str | list[str]]]]]:
        """Get a list of all API endpoints and return it."""
        endpoints: list[dict[str, str | list[dict[str, str | list[str]]]]] = []
        for module_info in self.settings["MODULE_INFOS"]:
            api_paths: list[dict[str, str | list[str]]] = [
                {
                    "path": handler[0],
                    "methods": handler[1].get_allowed_methods(),
                    "content_types": list(handler[1].POSSIBLE_CONTENT_TYPES),
                }
                for handler in module_info.handlers
                if handler[0].startswith("/api/")
                if issubclass(handler[1], APIRequestHandler)
                if (
                    handler[1].REQUIRED_PERMISSION is None
                    or self.is_authorized(handler[1].REQUIRED_PERMISSION)
                )
            ]
            if len(api_paths) > 0:
                endpoints.append(
                    {
                        "name": module_info.name,
                        "description": module_info.description,
                        "endpoints": api_paths,
                    }
                )
        return endpoints


class EndpointsAPI(APIRequestHandler, Endpoints):
    """Show a list of all API endpoints."""

    POSSIBLE_CONTENT_TYPES: ClassVar[
        tuple[str, ...]
    ] = APIRequestHandler.POSSIBLE_CONTENT_TYPES + ("application/x-ndjson",)

    async def get(self, *, head: bool = False) -> None:
        """Handle a GET request."""
        if self.content_type == "application/x-ndjson":
            await self.finish(
                b"\n".join(
                    json.dumps(endpoint, option=ORJSON_OPTIONS)
                    for endpoint in self.get_endpoints()
                )
            )
        else:
            await self.finish(self.dump(self.get_endpoints()))
