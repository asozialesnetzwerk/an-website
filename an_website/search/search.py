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

"""The search page used to search the website."""
from __future__ import annotations

import asyncio
import logging

import elasticapm  # type: ignore
import orjson as json

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/suche", Search),
            (r"/api/suche", SearchAPIHandler),
        ),
        name="Suche",
        description="Seite zum Durchsuchen der Webseite",
        aliases=("/search",),
        keywords=("Suche",),
        path="/suche",
    )


class Search(HTMLRequestHandler):
    """The Tornado request handler for the search page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the search page."""
        if head:
            return
        await self.render(
            "pages/search.html",
            query=self.get_query(),
            results=await self.search(),
        )

    def get_query(self) -> str:
        """Return the query."""
        return str(self.get_query_argument("q", strip=True, default=""))

    async def search(self) -> list[dict[str, float | str]]:
        """Search the website."""
        if query := self.get_query():
            try:
                return await self.app_search(query)
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception(exc)
                apm: None | elasticapm.Client = self.settings.get(
                    "ELASTIC_APM_CLIENT"
                )
                if apm:
                    apm.capture_exception()
        return await self.old_fallback_search(query)

    async def app_search(self, query: str) -> list[dict[str, float | str]]:
        """Search the website using Elastic App Search."""
        return [
            {
                "url": self.fix_url(result["url_path"]["raw"]),
                "title": result["title"]["snippet"],
                "description": result["meta_description"]["snippet"],
                "score": result["_meta"]["score"],
            }
            for result in (
                await asyncio.to_thread(
                    self.settings["APP_SEARCH"].search,
                    self.settings["APP_SEARCH_ENGINE_NAME"],
                    body={
                        "query": query,
                        "filters": {
                            "none": {
                                "quote_rating": {
                                    "to": 1,
                                },
                            },
                        },
                        "result_fields": {
                            "title": {
                                "snippet": {
                                    "size": 50,
                                    "fallback": True,
                                }
                            },
                            "meta_description": {
                                "snippet": {
                                    "size": 200,
                                    "fallback": True,
                                }
                            },
                            "url_path": {
                                "raw": {},
                            },
                        },
                    },
                )
            )["results"]
        ]

    async def old_fallback_search(
        self, query: str
    ) -> list[dict[str, float | str]]:
        """Search the website using the old search engine."""
        page_infos: list[tuple[float, list[tuple[str, float | str]]]] = []

        for module_info in self.get_module_infos():
            score = module_info.search(query)
            if score > 0:
                page_infos.append(
                    (
                        score,
                        [
                            ("url", self.fix_url(module_info.path)),
                            ("title", module_info.name),
                            ("description", module_info.description),
                            ("score", score),
                        ],
                    )
                )
            for sub_page in module_info.sub_pages:
                score = sub_page.search(query)
                if score > 0:
                    page_infos.append(
                        (
                            score,
                            [
                                ("url", self.fix_url(sub_page.path)),
                                ("title", sub_page.name),
                                ("description", sub_page.description),
                                ("score", score),
                            ],
                        )
                    )

        page_infos.sort(reverse=True)

        return [dict(info) for _, info in page_infos]


class SearchAPIHandler(Search, APIRequestHandler):
    """The Tornado request handler for the search API."""

    IS_NOT_HTML = True

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the search page."""
        if head:
            return
        await self.finish(json.dumps(await self.search()))
