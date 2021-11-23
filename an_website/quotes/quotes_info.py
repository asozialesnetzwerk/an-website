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
        handlers=(
            (r"/zitate/info/a/([0-9]{1,10})/", AuthorsInfoPage),
            (r"/zitate/info/z/([0-9]{1,10})/", QuotesInfoPage),
        ),
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
    # try to get the info from wikipedia
    response = await HTTP_CLIENT.fetch(
        f"{WIKI_API}?action=opensearch&namespace=0&profile=normal&"
        f"search={quote_url(query)}&limit=1&redirects=resolve&format=json"
    )
    response_json = json.loads(response.body)
    if len(response_json[1]) == 0:
        return None  # nothing found
    page_name = response_json[1][0]
    # get the url of the content & replace "," with "%2C"
    url = str(response_json[3][0]).replace(",", "%2C")

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

    RATELIMIT_NAME = "quote_info"

    async def get(self, _id_str: str):
        """Handle GET requests to the quote info page."""
        _id: int = int(_id_str)
        quote = await get_quote_by_id(_id)
        wqs = get_wrong_quotes(lambda _wq: _wq.quote.id == _id, True)
        await self.render(
            "pages/quotes/quote_info.html",
            quote=quote,
            wrong_quotes=wqs,
        )


class AuthorsInfoPage(BaseRequestHandler):
    """The request handler used for the info page."""

    RATELIMIT_NAME = "quote_info"
    RATELIMIT_TOKENS = 5

    def get_redis_info_key(self, author_name) -> str:
        """Get the key to save the author info with Redis."""
        prefix = self.settings.get("REDIS_PREFIX")
        return f"{prefix}:quote_author_info:{author_name}"

    async def get(self, _id_str: str):
        """Handle GET requests to the author info page."""
        _id: int = int(_id_str)
        author = await get_author_by_id(_id)
        if author.info is None:
            result = None
            if "REDIS" in self.settings:
                # try to get the info from Redis
                result = await self.settings["REDIS"].get(
                    self.get_redis_info_key(author.name)
                )
            if result:
                info: list[str] = result.decode("utf-8").split(",", maxsplit=1)
                if len(info) == 1:
                    author.info = (info[0], None)
                else:
                    author.info = (info[0], info[1])
            else:
                author.info = await search_wikipedia(author.name)
                if (
                    "REDIS" in self.settings
                    and author.info is not None
                    and author.info[1] is not None
                ):
                    await self.settings["REDIS"].setex(
                        self.get_redis_info_key(author.name),
                        60 * 60 * 24 * 30,  # time to live in seconds (1 month)
                        # value to save (the author info)
                        # type is ignored, because author.info[1] is not None
                        ",".join(author.info),  # type: ignore
                    )

        wqs = get_wrong_quotes(lambda _wq: _wq.author.id == _id, True)

        await self.render(
            "pages/quotes/author_info.html",
            author=author,
            wrong_quotes=wqs,
        )
