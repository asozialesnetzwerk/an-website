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

"""The quotes page of the website."""
from __future__ import annotations

import asyncio
import datetime
import logging
import os
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Literal, Optional

import orjson as json
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from ..utils.request_handler import BaseRequestHandler

DIR = os.path.dirname(__file__)

logger = logging.getLogger(__name__)

API_URL: str = "https://zitate.prapsschnalinen.de/api"

QUOTES_CACHE: dict[int, Quote] = {}
AUTHORS_CACHE: dict[int, Author] = {}
WRONG_QUOTES_CACHE: dict[tuple[int, int], WrongQuote] = {}

MAX_QUOTES_ID: list[int] = [0]
MAX_AUTHORS_ID: list[int] = [0]


@dataclass
class QuotesObjBase:
    """An object with an id."""

    id: int  # pylint: disable=invalid-name

    def get_id_as_str(self):
        """Get the id of the object as a string."""
        return str(self.id)

    def __str__(self):
        """Return a basic string with the id."""
        return f"QuotesObj({self.id})"


@dataclass
class Author(QuotesObjBase):
    """The author object with a name."""

    name: str
    # tuple(url_to_info, info_str)
    info: Optional[tuple[str, Optional[str], datetime.date]] = None

    def update_name(self, name: str):
        """Update author data with another author."""
        if self.name != name:
            # name changed -> info should change too
            self.info = None
            self.name = name

    def __str__(self):
        """Return the name of the author."""
        return self.name.strip()


@dataclass
class Quote(QuotesObjBase):
    """The quote object with a quote text and an author."""

    quote: str
    author: Author

    def update_quote(self, quote: str, author_id: int, author_name: str):
        """Update quote data with new data."""
        self.quote = quote
        if self.author.id == author_id:
            self.author.update_name(author_name)
            return
        self.author = get_author_updated_with(author_id, author_name)

    def __str__(self):
        """Return the the content of the quote."""
        return self.quote.strip()


@dataclass
class WrongQuote(QuotesObjBase):
    """The wrong quote object with a quote, an author and a rating."""

    quote: Quote
    author: Author
    rating: int

    def get_id(self) -> tuple[int, int]:
        """
        Get the id of the quote and the author in a tuple.

        :return tuple(quote_id, author_id)
        """
        return self.quote.id, self.author.id

    def get_id_as_str(self):
        """
        Get the id of the wrong quote as a string.

        Format: quote_id-author_id
        """
        return f"{self.quote.id}-{self.author.id}"

    def __str__(self):
        r"""
        Return the wrong quote.

        like: '»quote«\n - author'.
        """
        return f"»{self.quote}« - {self.author}"


def get_wrong_quotes(
    filter_fun: Optional[Callable[[WrongQuote], bool]] = None,
    sort: bool = False,  # sorted by rating
    filter_real_quotes: bool = True,
) -> tuple[WrongQuote, ...]:
    """Get cached wrong quotes."""
    wqs: Iterable[WrongQuote] = WRONG_QUOTES_CACHE.values()
    if filter_fun is not None:
        wqs = filter(filter_fun, wqs)
    if filter_real_quotes:
        wqs = filter(lambda _wq: _wq.quote.author.id != _wq.author.id, wqs)
    if not sort:
        return tuple(wqs)

    wqs_list = list(wqs)
    wqs_list.sort(key=lambda _wq: _wq.rating, reverse=True)
    return tuple(wqs_list)


HTTP_CLIENT = AsyncHTTPClient()


async def make_api_request(
    end_point: str,
    args: str = str(),
    method: Literal["GET", "POST"] = "GET",
    body: str = None,
) -> dict:
    """Make API request and return the result as dict."""
    response = await HTTP_CLIENT.fetch(
        f"{API_URL}/{end_point}?{args}",
        raise_error=False,
        method=method,
        body=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.code != 200:
        logger.error(
            "%s request to '%s/%s?%s' with body='%s' "
            "failed with code=%d and reason='%s'",
            method,
            API_URL,
            end_point,
            args,
            body,
            response.code,
            response.reason,
        )
        raise HTTPError(
            400,
            reason=f"{API_URL}/{end_point} returned: '{response.reason}'",
        )
    return json.loads(response.body)


def get_author_updated_with(author_id: int, author_name: str):
    """Get the author with the given id and the name."""
    author_name = author_name.strip()
    if len(author_name) == 0:
        author_name = "None"
    author = AUTHORS_CACHE.setdefault(
        author_id,
        Author(author_id, author_name),
    )
    author.update_name(author_name)
    MAX_AUTHORS_ID[0] = max(MAX_AUTHORS_ID[0], author_id)
    return author


def parse_author(json_data: dict) -> Author:
    """Parse a author from JSON data."""
    return get_author_updated_with(int(json_data["id"]), json_data["author"])


def fix_quote_str(quote_str: str) -> str:
    """Fix common mistakes in quotes."""
    if (
        len(quote_str) > 2
        and (quote_str.startswith('"') or quote_str.startswith("„"))
        and (quote_str.endswith('"') or quote_str.endswith("“"))
    ):
        # remove double quotes from quote,
        # that are stupid and shouldn't be there
        quote_str = quote_str[1:-1]

    return quote_str.strip()


def parse_quote(json_data: dict) -> Quote:
    """Parse a quote from JSON data."""
    quote_id = int(json_data["id"])
    author = parse_author(json_data["author"])
    quote_str = fix_quote_str(json_data["quote"])

    quote = QUOTES_CACHE.setdefault(
        quote_id,
        Quote(
            quote_id,
            quote_str,
            author,
        ),
    )

    MAX_QUOTES_ID[0] = max(MAX_QUOTES_ID[0], quote.id)

    quote.update_quote(
        quote_str,
        author.id,
        author.name,
    )
    return quote


def parse_wrong_quote(json_data: dict) -> WrongQuote:
    """Parse a quote."""
    id_tuple = (int(json_data["quote"]["id"]), int(json_data["author"]["id"]))
    rating = json_data["rating"]
    wrong_quote_id = int(json_data.get("id", -1))
    if wrong_quote_id is None:
        wrong_quote_id = -1
    wrong_quote = WRONG_QUOTES_CACHE.setdefault(
        id_tuple,
        WrongQuote(
            id=wrong_quote_id,
            quote=parse_quote(json_data["quote"]),
            author=parse_author(json_data["author"]),
            rating=rating,
        ),
    )
    assert (wrong_quote.quote.id, wrong_quote.author.id) == id_tuple
    if wrong_quote.rating != rating:
        wrong_quote.rating = rating
    if wrong_quote.id != wrong_quote_id:
        wrong_quote.id = wrong_quote_id
    return wrong_quote


async def start_updating_cache_periodically(app):
    """Start updating the cache every hour."""
    redis = app.settings.get("REDIS")
    prefix = app.settings.get("REDIS_PREFIX")
    if redis:
        wrongquotes = await redis.get(
            f"{prefix}:cached-quote-data:wrongquotes"
        )
        if wrongquotes:
            for _wq in json.loads(wrongquotes.decode("utf-8")):
                parse_wrong_quote(_wq)
        quotes = await redis.get(f"{prefix}:cached-quote-data:quotes")
        if quotes:
            for _q in json.loads(quotes.decode("utf-8")):
                parse_quote(_q)
        authors = await redis.get(f"{prefix}:cached-quote-data:authors")
        if authors:
            for _a in json.loads(authors.decode("utf-8")):
                parse_author(_a)
    while True:
        await update_cache(redis, prefix)
        await asyncio.sleep(60 * 60)


async def update_cache(redis=None, redis_prefix=None):
    """Fill the cache with all data from the API."""
    logger.info("Update quotes cache.")
    wq_data = await make_api_request("wrongquotes")
    for wrong_quote in wq_data:
        parse_wrong_quote(wrong_quote)
    if wq_data and redis:
        await redis.set(
            f"{redis_prefix}:cached-quote-data:wrongquotes",
            json.dumps(wq_data),
        )
    quotes_data = await make_api_request("quotes")
    for quote in quotes_data:
        parse_quote(quote)
    if quotes_data and redis:
        await redis.set(
            f"{redis_prefix}:cached-quote-data:quotes",
            json.dumps(quotes_data),
        )

    authors_data = await make_api_request("authors")
    for author in authors_data:
        parse_author(author)
    if authors_data and redis:
        await redis.set(
            f"{redis_prefix}:cached-quote-data:authors",
            json.dumps(authors_data),
        )


async def get_author_by_id(author_id: int) -> Author:
    """Get an author by its id."""
    author = AUTHORS_CACHE.get(author_id, None)
    if author is not None:
        return author

    return parse_author(await make_api_request(f"authors/{author_id}"))


async def get_quote_by_id(quote_id: int) -> Quote:
    """Get a quote by its id."""
    quote = QUOTES_CACHE.get(quote_id, None)
    if quote is not None:
        return quote
    return parse_quote(await make_api_request(f"quotes/{quote_id}"))


async def get_wrong_quote(
    quote_id: int, author_id: int, use_cache=True
) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    wrong_quote_id = (quote_id, author_id)
    wrong_quote = WRONG_QUOTES_CACHE.get(wrong_quote_id, None)
    if use_cache and wrong_quote is not None:
        return wrong_quote

    if not use_cache and wrong_quote is not None and wrong_quote.id != -1:
        # use the id of the wrong quote to get the data more efficient
        return parse_wrong_quote(
            await make_api_request(f"wrongquotes/{wrong_quote.id}")
        )
    if use_cache and quote_id in QUOTES_CACHE and author_id in AUTHORS_CACHE:
        # we don't need to request anything, as the wrong_quote probably has
        # no ratings just use the cached quote and author
        return WrongQuote(
            -1,
            QUOTES_CACHE[quote_id],
            AUTHORS_CACHE[author_id],
            0,
        )
    result = await make_api_request(
        "wrongquotes",
        f"quote={quote_id}&author={author_id}&simulate=true",
    )
    if len(result) > 0:
        return parse_wrong_quote(result[0])

    return WrongQuote(
        -1,
        await get_quote_by_id(quote_id),
        await get_author_by_id(author_id),
        rating=0,
    )


async def get_rating_by_id(quote_id: int, author_id: int) -> int:
    """Get the rating of a wrong quote."""
    return (await get_wrong_quote(quote_id, author_id)).rating


def get_random_quote_id() -> int:
    """Get random quote id."""
    return random.randint(1, MAX_QUOTES_ID[0])


def get_random_author_id() -> int:
    """Get random author id."""
    return random.randint(1, MAX_AUTHORS_ID[0])


def get_random_id() -> tuple[int, int]:
    """Get random wrong quote id."""
    return (
        get_random_quote_id(),
        get_random_author_id(),
    )


async def vote_wrong_quote(
    vote: Literal[-1, 1], wrong_quote: WrongQuote
) -> WrongQuote:
    """Vote for the wrong_quote with the given id."""
    return parse_wrong_quote(
        await make_api_request(
            f"wrongquotes/{wrong_quote.id}",
            method="POST",
            body=f"vote={vote}",
        )
    )


def vote_wrong_quote_fast(
    vote: Literal[-1, 1], wrong_quote: WrongQuote
) -> WrongQuote:
    """Vote for the wrong_quote with the given id."""
    wrong_quote.rating += vote
    asyncio.create_task(vote_wrong_quote(vote, wrong_quote))
    return wrong_quote


async def create_wq_and_vote(
    vote: Literal[-1, 1],
    quote_id: int,
    author_id: int,
    contributed_by: str,
    fast: bool = False,
) -> WrongQuote:
    """
    Vote for the wrong_quote with the API.

    If the wrong_quote doesn't exist yet, create it.
    """
    wrong_quote = WRONG_QUOTES_CACHE.get((quote_id, author_id), None)
    if wrong_quote is not None and wrong_quote.id != -1:
        if fast:
            return vote_wrong_quote_fast(vote, wrong_quote)
        return await vote_wrong_quote(vote, wrong_quote)
    # we don't know the wrong_quote_id, so we have to create the wrong_quote
    wrong_quote = parse_wrong_quote(
        await make_api_request(
            "wrongquotes",
            method="POST",
            body=f"quote={quote_id}&author={author_id}&"
            f"contributed_by={contributed_by}",
        )
    )
    return vote_wrong_quote_fast(vote, wrong_quote)


class QuoteReadyCheckRequestHandler(BaseRequestHandler):
    """Class that checks if quotes have been loaded."""

    RATELIMIT_NAME = "quotes"

    async def prepare(self):
        """Fail if quotes aren't ready yet."""
        if len(WRONG_QUOTES_CACHE) == 0:
            # should work in a few seconds, the quotes just haven't loaded yet
            self.set_header("Retry-After", "3")
            raise HTTPError(503, reason="Service available in a few seconds.")
        await super().prepare()
