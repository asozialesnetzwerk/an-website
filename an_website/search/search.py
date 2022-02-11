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

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo, PageInfo

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/suche/", Search),),
        name="Suche",
        description="Seite zum Durchsuchen der Webseite",
        aliases=("/search/",),
        keywords=("Suche",),
        path="/suche/",
        hidden=True,
    )


class Search(HTMLRequestHandler):
    """The Tornado request handler for the search page."""

    async def get(self) -> None:
        """Handle GET requests to the search page."""
        query = str(self.get_query_argument("q", strip=True, default=""))

        try:
            results = [
                {
                    "url": self.fix_url(result["url_path"]["raw"]),
                    "title": result["title"].get("snippet")
                    or result["title"]["raw"],
                    "description": result["meta_description"].get("snippet")
                    or result["meta_description"]["raw"],
                    "score": result["_meta"]["score"],
                }
                for result in (
                    await asyncio.to_thread(
                        self.settings["APP_SEARCH"].search,
                        self.settings["APP_SEARCH_ENGINE_NAME"],
                        body={"query": query},  # TODO: try to filter response
                    )
                )["results"]
            ]
        except Exception as exc:  # pylint: disable=broad-except  # TODO: Fix
            logger.exception(exc)
            return await self.old_fallback_search(query)

        await self.render(
            "pages/search.html",
            query=query,
            results=results,
        )

    async def old_fallback_search(self, query: str) -> None:
        """Search the website using the old search engine."""
        module_infos: list[
            tuple[float, ModuleInfo, list[tuple[float, PageInfo]]]
        ] = []

        for module_info in self.get_module_infos():
            score = module_info.search(query)
            if score > 0:
                sub_pages = [
                    (score, sub_page)
                    for sub_page in module_info.sub_pages
                    if (score := sub_page.search(query)) > 0
                ]
                sub_pages.sort(reverse=True)
                module_infos.append((score, module_info, sub_pages))

        module_infos.sort(reverse=True)

        results = [
            {
                "url": self.fix_url(info.path),
                "title": info.name,
                "description": info.description,
                "score": score,
                "sub_pages": sub_pages,
            }
            for score, info, sub_pages in module_infos
        ]

        await self.render(
            "pages/search.html",
            query=query,
            results=results,
        )
