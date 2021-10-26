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

"""Info-page to show information about authors and quotes."""
from __future__ import annotations

from typing import Optional
from urllib.parse import quote as quote_url

import orjson as json

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo
from . import HTTP_CLIENT, get_author_by_id, get_quote_by_id, get_wrong_quotes


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/zitate/info/([aq])/([0-9]{1,10})/", QuotesInfoPage),),
        name="Falsche Zitate",
        description="Eine Webseite mit falsch zugeordneten Zitaten",
        path="/zitate/info/a/1/",
        hidden=True,
    )


WIKI_API = "https://de.wikipedia.org/w/api.php"


async def search_wikipedia(query: str) -> Optional[tuple[str, Optional[str]]]:
    """
    Search wikipedia to get information about the query.

    Return a tuple with the url and the content.
    """
    if len(query) == 0:
        return None
    response = await HTTP_CLIENT.fetch(
        f"{WIKI_API}?action=opensearch&namespace=0&profile=normal&"
        f"search={quote_url(query)}&limit=1&redirects=resolve&format=json"
    )
    response_json = json.loads(response.body)
    if len(response_json[1]) == 0:
        return None  # nothing found
    page_name = response_json[1][0]
    url = str(response_json[3][0])

    return url, await get_wikipedia_page_content(page_name)


async def get_wikipedia_page_content(page_name: str) -> Optional[str]:
    """Get content from a wikipedia page and return it."""
    response = await HTTP_CLIENT.fetch(
        f"{WIKI_API}?action=query&prop=extracts&exsectionformat=plain&exintro&"
        f"titles={quote_url(page_name)}&explaintext&format=json&exsentences=5"
    )
    response_json = json.loads(response.body)
    if "query" not in response_json or "pages" not in response_json["query"]:
        return None
    pages: dict = response_json["query"]["pages"]
    page = tuple(pages.values())[0]
    if "extract" not in page:
        return None
    return page["extract"]


class QuotesInfoPage(BaseRequestHandler):
    """The request handler used for the info page."""

    async def get(self, a_or_q: str, _id: str):
        """Handle get requests to the info page."""
        if a_or_q == "a":
            return await self.author_info(int(_id))
        if a_or_q == "q":
            return await self.quote_info(int(_id))

    async def author_info(self, _id: int):
        """Show author info."""
        author = await get_author_by_id(_id)
        if author.info is None:
            author.info = await search_wikipedia(author.name)

        wqs = get_wrong_quotes(lambda _wq: _wq.author.id == _id, True)

        await self.render(
            "pages/quotes/author_info.html",
            author=author,
            wrong_quotes=wqs,
        )

    async def quote_info(self, _id: int):
        """Show quote info."""
        quote = await get_quote_by_id(_id)
        wqs = get_wrong_quotes(lambda _wq: _wq.quote.id == _id, True)
        await self.render(
            "pages/quotes/quote_info.html",
            quote=quote,
            wrong_quotes=wqs,
        )
