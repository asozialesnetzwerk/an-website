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
from collections.abc import Sequence
from typing import Final, Literal, TypeAlias, cast

import orjson as json
from elastic_enterprise_search import AppSearch  # type: ignore[import]

from .. import NAME
from ..quotes.utils import Author, Quote, get_authors, get_quotes
from ..utils import search
from ..utils.decorators import get_setting_or_default, requires_settings
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import AwaitableValue, ModuleInfo

LOGGER: Final = logging.getLogger(__name__)

UnscoredPageInfo: TypeAlias = tuple[
    tuple[Literal["url"], str],
    tuple[Literal["title"], str],
    tuple[Literal["description"], str],
]
OldSearchPageInfo: TypeAlias = search.ScoredValue[UnscoredPageInfo]


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
    """The request handler for the search page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the search page."""
        if head:
            return
        print(await self.search())
        await self.render(
            "pages/search.html",
            query=self.get_query(),
            results=await self.search(),
        )

    def get_query(self) -> str:
        """Return the query."""
        return str(self.get_argument("q", ""))

    async def search(self) -> list[dict[str, float | str]]:
        """Search the website."""
        result: list[dict[str, str | float]] | None = None
        if query := self.get_query():
            try:
                result = await self.search_new(query)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("App Search request failed")
                if self.apm_client:
                    self.apm_client.capture_exception()
        if result is not None:
            return result
        return self.search_old(query)

    @requires_settings("APP_SEARCH", return_=AwaitableValue(None))
    @get_setting_or_default("APP_SEARCH_ENGINE", NAME.removesuffix("-dev"))
    async def search_new(  # type: ignore[no-any-unimported]
        self,
        query: str,
        *,
        app_search: AppSearch = ...,
        app_search_engine: str = ...,  # type: ignore[assignment]
    ) -> list[dict[str, str | float]] | None:
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
                    app_search.search,
                    app_search_engine,
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

    def search_old(self, query: str) -> list[dict[str, str | float]]:
        """Search the website using the old search engine."""
        page_infos: list[OldSearchPageInfo] = []

        for module_info in self.get_module_infos():
            score = module_info.search(query)
            if score > 0:
                page_infos.append(
                    search.ScoredValue(
                        score,
                        (
                            ("url", self.fix_url(module_info.path)),
                            ("title", module_info.name),
                            ("description", module_info.description),
                        ),
                    )
                )
            for sub_page in module_info.sub_pages:
                score = sub_page.search(query)
                if score > 0:
                    page_infos.append(
                        search.ScoredValue(
                            score,
                            (
                                ("url", self.fix_url(sub_page.path)),
                                ("title", sub_page.name),
                                ("description", sub_page.description),
                            ),
                        )
                    )

        if query:
            page_infos.extend(self.search_authors_and_quotes(query))

        page_infos.sort(reverse=True)

        return [
            dict(scored_value.value + (("score", scored_value.score),))
            for scored_value in page_infos
        ]

    def search_authors_and_quotes(
        self, query: str
    ) -> Sequence[OldSearchPageInfo]:
        """Search authors and quotes."""
        if not (query_object := search.Query(query)):
            return ()
        authors: search.DataProvider[
            Author, UnscoredPageInfo
        ] = search.DataProvider(
            get_authors,
            lambda author: author.name,
            lambda a: (
                ("url", self.fix_url(a.get_path())),
                ("title", "Autoren-Info"),
                ("description", a.name),
            ),
        )
        quotes: search.DataProvider[
            Quote, UnscoredPageInfo
        ] = search.DataProvider(
            get_quotes,
            lambda quote: (quote.quote, quote.author.name),
            lambda q: (
                ("url", self.fix_url(q.get_path())),
                ("title", "Zitat-Info"),
                ("description", str(q)),
            ),
        )
        return search.search(
            query_object,
            cast(search.DataProvider[object, UnscoredPageInfo], authors),
            cast(search.DataProvider[object, UnscoredPageInfo], quotes),
        )


class SearchAPIHandler(APIRequestHandler, Search):
    """The request handler for the search API."""

    IS_NOT_HTML = True

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the search page."""
        if head:
            return
        await self.finish(json.dumps(await self.search()))
