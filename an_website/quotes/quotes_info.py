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

import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote as quote_url

import orjson as json

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo
from . import (
    HTTP_CLIENT,
    get_author_by_id,
    get_quote_by_id,
    get_wrong_quotes,
    logger,
)


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


class QuotesInfoPage(BaseRequestHandler):
    """The request handler used for the info page."""

    RATELIMIT_NAME = "quotes-info"

    async def get(self, _id_str: str):
        """Handle GET requests to the quote info page."""
        _id: int = int(_id_str)
        quote = await get_quote_by_id(_id)
        wqs = get_wrong_quotes(lambda _wq: _wq.quote.id == _id, sort=True)
        await self.render(
            "pages/quotes/quote_info.html",
            quote=quote,
            wrong_quotes=wqs,
            title="Zitat-Informationen",
            description=f"Falsche Zitate mit „{quote.quote}“ als Zitat.",
        )


WIKI_API_DE = "https://de.wikipedia.org/w/api.php"
WIKI_API_EN = "https://en.wikipedia.org/w/api.php"


async def search_wikipedia(
    query: str, api: str = WIKI_API_DE
) -> Optional[tuple[str, Optional[str], datetime]]:
    """
    Search wikipedia to get information about the query.

    Return a tuple with the url and the content.
    """
    if len(query) == 0:
        return None
    # try to get the info from wikipedia
    response = await HTTP_CLIENT.fetch(
        f"{api}?action=opensearch&namespace=0&profile=normal&"
        f"search={quote_url(query)}&limit=1&redirects=resolve&format=json"
    )
    response_json = json.loads(response.body)
    if len(response_json[1]) == 0:
        if api == WIKI_API_DE:
            return await search_wikipedia(query, WIKI_API_EN)
        return None  # nothing found
    page_name = response_json[1][0]
    # get the url of the content & replace "," with "%2C"
    url = str(response_json[3][0]).replace(",", "%2C")

    return (
        url,
        await get_wikipedia_page_content(page_name, api),
        datetime.now(timezone.utc),
    )


async def get_wikipedia_page_content(
    page_name: str, api: str = WIKI_API_DE
) -> Optional[str]:
    """Get content from a wikipedia page and return it."""
    response = await HTTP_CLIENT.fetch(
        f"{api}?action=query&prop=extracts&exsectionformat=plain&exintro&"
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


def fix_author_for_wikipedia_search(author: str) -> str:
    """
    Fix author for wikipedia search.

    This tries to reduce common problems with authors.
    So that we can show more information.
    """
    author = re.sub(r"\s+", " ", author)
    author = re.sub(r"\s*\(.*\)", str(), author)
    author = re.sub(r"\s*Werbespruch$", str(), author, flags=re.IGNORECASE)
    author = re.sub(r"\s*Werbung$", str(), author, flags=re.IGNORECASE)
    author = re.sub(r"^nach\s*", str(), author, flags=re.IGNORECASE)
    author = re.sub(r"^Ein\s+", str(), author, flags=re.IGNORECASE)
    return author


# time to live in seconds (1 month)
AUTHOR_INFO_NEW_TTL = 60 * 60 * 24 * 30


class AuthorsInfoPage(BaseRequestHandler):
    """The request handler used for the info page."""

    RATELIMIT_NAME = "quotes-info"
    RATELIMIT_TOKENS = 5

    def get_redis_info_key(self, author_name) -> str:
        """Get the key to save the author info with Redis."""
        prefix = self.settings.get("REDIS_PREFIX")
        return f"{prefix}:quote-author-info:{author_name}"

    async def get(self, _id_str: str):
        """Handle GET requests to the author info page."""
        _id: int = int(_id_str)
        author = await get_author_by_id(_id)
        if author.info is None:
            result = None
            redis = self.settings.get("REDIS")
            fixed_author_name = fix_author_for_wikipedia_search(author.name)
            if redis is not None:
                # try to get the info from Redis
                result = await redis.get(
                    self.get_redis_info_key(fixed_author_name)
                )
            if result:
                info: list[str] = result.decode("utf-8").split("|", maxsplit=1)
                remaining_ttl = await redis.ttl(
                    self.get_redis_info_key(fixed_author_name)
                )
                creation_date = datetime.now(tz=timezone.utc) - timedelta(
                    seconds=AUTHOR_INFO_NEW_TTL - remaining_ttl
                )
                if len(info) == 1:
                    author.info = (info[0], None, creation_date)
                else:
                    author.info = (info[0], info[1], creation_date)
            else:
                author.info = await search_wikipedia(fixed_author_name)
                if author.info is None or author.info[1] is None:
                    # nothing found
                    logger.info("No information found about %s", repr(author))
                elif redis is not None:
                    await redis.setex(
                        self.get_redis_info_key(fixed_author_name),
                        AUTHOR_INFO_NEW_TTL,
                        # value to save (the author info)
                        # type is ignored, because author.info[1] is not None
                        "|".join(author.info[0:2]),  # type: ignore
                    )

        wqs = get_wrong_quotes(
            lambda _wq: _wq.author.id == _id,
            sort=True,
        )

        await self.render(
            "pages/quotes/author_info.html",
            author=author,
            wrong_quotes=wqs,
            title="Autor-Informationen",
            description=f"Falsche Zitate mit „{author.name}“ als Autor.",
        )
