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

"""Info page to show information about authors and quotes."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Final, cast
from urllib.parse import quote as quote_url

import orjson as json
import regex
from tornado.httpclient import AsyncHTTPClient

from .. import DIR as ROOT_DIR
from .. import EVENT_REDIS
from ..utils.request_handler import HTMLRequestHandler
from .utils import get_author_by_id, get_quote_by_id, get_wrong_quotes

LOGGER: Final = logging.getLogger(__name__)


class QuotesInfoPage(HTMLRequestHandler):
    """The request handler used for the info page."""

    RATELIMIT_GET_LIMIT = 30

    async def get(self, id_str: str, *, head: bool = False) -> None:
        """Handle GET requests to the quote info page."""
        quote_id: int = int(id_str)
        quote = await get_quote_by_id(quote_id)
        if head:
            return
        wqs = get_wrong_quotes(lambda wq: wq.quote.id == quote_id, sort=True)
        await self.render(
            "pages/quotes/quote_info.html",
            quote=quote,
            wrong_quotes=wqs,
            title="Zitat-Informationen",
            short_title="Zitat-Info",
            type="Zitat",
            id=quote_id,
            text=str(quote),
            description=f"Falsch zugeordnete Zitate mit „{quote}“ als Zitat.",
            create_kwargs={"quote": quote_id},
        )


WIKI_API_DE: Final[str] = "https://de.wikipedia.org/w/api.php"
WIKI_API_EN: Final[str] = "https://en.wikipedia.org/w/api.php"


async def search_wikipedia(
    query: str, api: str = WIKI_API_DE
) -> None | tuple[str, None | str, datetime]:
    """
    Search Wikipedia to get information about the query.

    Return a tuple with the URL and the content.
    """
    if not query:
        return None
    # try to get the info from Wikipedia
    response = await AsyncHTTPClient().fetch(
        (
            f"{api}?action=opensearch&namespace=0&profile=normal&"
            f"search={quote_url(query)}&limit=1&redirects=resolve&format=json"
        ),
        ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
    )
    response_json = json.loads(response.body)
    if not response_json[1]:
        if api == WIKI_API_DE:
            return await search_wikipedia(query, WIKI_API_EN)
        return None  # nothing found
    page_name = response_json[1][0]
    # get the URL of the content & replace "," with "%2C"
    url = str(response_json[3][0]).replace(",", "%2C")

    return (
        url,
        await get_wikipedia_page_content(page_name, api),
        datetime.now(timezone.utc),
    )


async def get_wikipedia_page_content(
    page_name: str, api: str = WIKI_API_DE
) -> None | str:
    """Get content from a Wikipedia page and return it."""
    response = await AsyncHTTPClient().fetch(
        (
            f"{api}?action=query&prop=extracts&exsectionformat=plain&exintro&"
            f"titles={quote_url(page_name)}&explaintext&format=json&exsentences=5"
        ),
        ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
    )
    response_json = json.loads(response.body)
    if "query" not in response_json or "pages" not in response_json["query"]:
        return None
    pages: dict[str, str] = response_json["query"]["pages"]
    page = cast(dict[str, str], tuple(pages.values())[0])
    if "extract" not in page:
        return None
    return page["extract"]


def fix_author_for_wikipedia_search(author: str) -> str:
    """
    Fix author for Wikipedia search.

    This tries to reduce common problems with authors.
    So that we can show more information.
    """
    author = regex.sub(r"\s+", " ", author)
    author = regex.sub(r"\s*\(.*\)", "", author)
    author = regex.sub(r"\s*Werbespruch$", "", author, regex.IGNORECASE)
    author = regex.sub(r"\s*Werbung$", "", author, regex.IGNORECASE)
    author = regex.sub(r"^nach\s*", "", author, regex.IGNORECASE)
    author = regex.sub(r"^Ein\s+", "", author, regex.IGNORECASE)
    return author


# time to live in seconds (1 month)
AUTHOR_INFO_NEW_TTL: Final[int] = 60 * 60 * 24 * 30


class AuthorsInfoPage(HTMLRequestHandler):
    """The request handler used for the info page."""

    RATELIMIT_GET_LIMIT = 5

    async def get(self, id_str: str, *, head: bool = False) -> None:
        """Handle GET requests to the author info page."""
        author_id: int = int(id_str)
        author = await get_author_by_id(author_id)
        if head:
            return
        if author.info is None:
            result = None
            fixed_author_name = fix_author_for_wikipedia_search(author.name)
            if EVENT_REDIS.is_set():
                # try to get the info from Redis
                result = await self.redis.get(
                    self.get_redis_info_key(fixed_author_name)
                )
            if result and (len(info := result.split("|", maxsplit=1)) > 1):
                remaining_ttl = await self.redis.ttl(
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
                    LOGGER.info("No information found about %s", repr(author))
                elif EVENT_REDIS.is_set():
                    await self.redis.setex(
                        self.get_redis_info_key(fixed_author_name),
                        AUTHOR_INFO_NEW_TTL,
                        # value to save (the author info)
                        # type is ignored, because author.info[1] is not None
                        "|".join(author.info[0:2]),  # type: ignore[arg-type]
                    )

        wqs = get_wrong_quotes(
            lambda wq: wq.author.id == author_id,
            sort=True,
        )

        await self.render(
            "pages/quotes/author_info.html",
            author=author,
            wrong_quotes=wqs,
            title="Autor-Informationen",
            short_title="Autor-Info",
            type="Autor",
            id=author_id,
            text=str(author),
            description=f"Falsch zugeordnete Zitate mit „{author}“ als Autor.",
            create_kwargs={"author": author_id},
        )

    def get_redis_info_key(self, author_name: str) -> str:
        """Get the key to save the author info with Redis."""
        return f"{self.redis_prefix}:quote-author-info:{author_name}"
