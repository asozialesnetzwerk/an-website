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
from typing import Any, Final, Literal, TypeAlias, cast

import orjson as json
from typed_stream import Stream

from .. import NAME
from ..quotes.utils import (
    Author,
    Quote,
    WrongQuote,
    get_authors,
    get_quotes,
    get_wrong_quotes,
)
from ..soundboard.data import ALL_SOUNDS, SoundInfo
from ..utils import search
from ..utils.decorators import get_setting_or_default, requires_settings
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import AwaitableValue, ModuleInfo, PageInfo

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

    def convert_page_info_to_simple_tuple(
        self, page_info: PageInfo
    ) -> UnscoredPageInfo:
        """Convert PageInfo to tuple of tuples."""
        return (
            ("url", self.fix_url(page_info.path)),
            ("title", page_info.name),
            ("description", page_info.description),
        )

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the search page."""
        if head:
            return
        await self.render(
            "pages/search.html",
            query=self.get_query(),
            results=await self.search(),
        )

    def get_all_page_info(self) -> Stream[PageInfo]:
        """Return all page infos that can be found."""
        return (
            Stream(self.get_module_infos())
            .flat_map(lambda mi: mi.sub_pages + (mi,))
            .exclude(lambda pi: pi.hidden)
            .filter(lambda pi: pi.path)
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
                    self.apm_client.capture_exception()  # type: ignore[no-untyped-call]
        if result is not None:
            return result
        return self.search_old(query)

    @requires_settings("APP_SEARCH", return_=AwaitableValue(None))
    @get_setting_or_default("APP_SEARCH_ENGINE", NAME.removesuffix("-dev"))
    async def search_new(
        self,
        query: str,
        *,
        app_search: Any = ...,
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

    def search_old(
        self, query: str, limit: int = 20
    ) -> list[dict[str, str | float]]:
        """Search the website using the old search engine."""
        page_infos = self.search_old_internal(query)

        page_infos.sort(reverse=True)

        return [
            dict(scored_value.value + (("score", scored_value.score),))
            for scored_value in page_infos[:limit]
        ]

    def search_old_internal(self, query: str) -> list[OldSearchPageInfo]:
        """Search authors and quotes."""
        if not (query_object := search.Query(query)):
            return list(
                self.get_all_page_info()
                .map(self.convert_page_info_to_simple_tuple)
                .map(lambda unscored: search.ScoredValue(1, unscored))
            )
        pages: search.DataProvider[PageInfo, UnscoredPageInfo] = (
            search.DataProvider(
                self.get_all_page_info,
                lambda page_info: (
                    page_info.name,
                    page_info.description,
                    *page_info.keywords,
                ),
                self.convert_page_info_to_simple_tuple,
            )
        )
        soundboard: search.DataProvider[SoundInfo, UnscoredPageInfo] = (
            search.DataProvider(
                ALL_SOUNDS,
                lambda sound_info: (
                    sound_info.text,
                    sound_info.person.value,
                ),
                lambda sound_info: (
                    (
                        "url",
                        self.fix_url(
                            f"/soundboard/{sound_info.person.name}#{sound_info.filename}"
                        ),
                    ),
                    ("title", f"Soundboard ({sound_info.person.value})"),
                    ("description", sound_info.text),
                ),
            )
        )
        authors: search.DataProvider[Author, UnscoredPageInfo] = (
            search.DataProvider(
                get_authors,
                lambda author: author.name,
                lambda author: (
                    ("url", self.fix_url(author.get_path())),
                    ("title", "Autoren-Info"),
                    ("description", author.name),
                ),
            )
        )
        quotes: search.DataProvider[Quote, UnscoredPageInfo] = (
            search.DataProvider(
                get_quotes,
                lambda quote: (quote.quote, quote.author.name),
                lambda q: (
                    ("url", self.fix_url(q.get_path())),
                    ("title", "Zitat-Info"),
                    ("description", str(q)),
                ),
            )
        )
        wrong_quotes: search.DataProvider[WrongQuote, UnscoredPageInfo] = (
            search.DataProvider(
                lambda: get_wrong_quotes(lambda wq: wq.rating > 0),
                lambda wq: (wq.quote.quote, wq.author.name),
                lambda wq: (
                    ("url", self.fix_url(wq.get_path())),
                    ("title", "Falsches Zitat"),
                    ("description", str(wq)),
                ),
            )
        )
        return search.search(
            query_object,
            cast(search.DataProvider[object, UnscoredPageInfo], pages),
            cast(search.DataProvider[object, UnscoredPageInfo], soundboard),
            cast(search.DataProvider[object, UnscoredPageInfo], authors),
            cast(search.DataProvider[object, UnscoredPageInfo], quotes),
            cast(search.DataProvider[object, UnscoredPageInfo], wrong_quotes),
        )


class SearchAPIHandler(APIRequestHandler, Search):
    """The request handler for the search API."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the search page."""
        if head:
            return
        await self.finish(json.dumps(await self.search()))
