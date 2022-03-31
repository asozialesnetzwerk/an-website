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

"""A page with wrong quotes."""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import random
import sys
import time
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any, Literal

import elasticapm  # type: ignore
import orjson as json
import tornado.web
from redis.asyncio import Redis  # type: ignore
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from .. import DIR as ROOT_DIR
from .. import ORJSON_OPTIONS
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import emojify

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

    # pylint: disable=unused-argument
    def get_id_as_str(self, minify: bool = False) -> str:
        """Get the id of the object as a string."""
        return str(self.id)

    async def fetch_new_data(self) -> QuotesObjBase:
        """Fetch new data from the API."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Return a basic string with the id."""
        return f"QuotesObj({self.id})"


@dataclass
class Author(QuotesObjBase):
    """The author object with a name."""

    name: str
    # tuple(url_to_info, info_str, creation_date)
    info: None | tuple[str, None | str, datetime.date] = None

    def update_name(self, name: str) -> None:
        """Update author data with another author."""
        if self.name != name:
            # name changed -> info should change too
            self.info = None
            self.name = name

    async def fetch_new_data(self) -> Author:
        """Fetch new data from the API."""
        return parse_author(await make_api_request(f"authors/{self.id}"))

    def to_json(self) -> dict[str, Any]:
        """Get the author as JSON."""
        return {
            "id": self.id,
            "name": str(self),
            "path": f"/zitate/info/a/{self.id}",
            "info": {
                "source": self.info[0],
                "text": self.info[1],
                "date": self.info[2].isoformat(),
            }
            if self.info
            else None,
        }

    def __str__(self) -> str:
        """Return the name of the author."""
        return (
            emojify(self.name.strip())
            if (now := datetime.datetime.utcnow()).day == 1 and now.month == 4
            else self.name.strip()
        )


@dataclass
class Quote(QuotesObjBase):
    """The quote object with a quote text and an author."""

    quote: str
    author: Author

    def update_quote(
        self, quote: str, author_id: int, author_name: str
    ) -> None:
        """Update quote data with new data."""
        self.quote = quote
        if self.author.id == author_id:
            self.author.update_name(author_name)
            return
        self.author = get_author_updated_with(author_id, author_name)

    async def fetch_new_data(self) -> Quote:
        """Fetch new data from the API."""
        return parse_quote(await make_api_request(f"quotes/{self.id}"))

    def to_json(self) -> dict[str, Any]:
        """Get the quote as JSON."""
        return {
            "id": self.id,
            "quote": str(self),
            "author": self.author.to_json(),
            "path": f"/zitate/info/z/{self.id}",
        }

    def __str__(self) -> str:
        """Return the content of the quote."""
        return (
            emojify(self.quote.strip())
            if (now := datetime.datetime.utcnow()).day == 1 and now.month == 4
            else self.quote.strip()
        )


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

    def get_id_as_str(self, minify: bool = False) -> str:
        """
        Get the id of the wrong quote as a string.

        Format: quote_id-author_id
        """
        if minify and self.id != -1:
            return str(self.id)
        return f"{self.quote.id}-{self.author.id}"

    async def fetch_new_data(self) -> WrongQuote:
        """Fetch new data from the API."""
        return parse_wrong_quote(
            (
                await make_api_request(
                    "wrongquotes",
                    f"quote={self.quote.id}"
                    f"&author={self.author.id}"
                    "&simulate=true",
                )
            )[0]
            if self.id == -1
            else await make_api_request(f"wrongquotes/{self.id}")
        )

    async def vote(
        self, vote: Literal[-1, 1], fast: bool = False
    ) -> WrongQuote:
        """Vote for the wrong quote."""
        if self.id == -1:
            raise ValueError("Can't vote for a not existing quote.")
        if fast:  # simulate the vote and do the actual voting later
            self.rating += vote
            asyncio.get_running_loop().call_soon_threadsafe(
                self.vote,
                vote,
                False,
            )
            return self
        # do the voting
        return parse_wrong_quote(
            await make_api_request(
                f"wrongquotes/{self.id}",
                method="POST",
                body=f"vote={vote}",
            )
        )

    def to_json(self) -> dict[str, Any]:
        """Get the wrong quote as JSON."""
        return {
            "id": self.get_id_as_str(),
            "quote": self.quote.to_json(),
            "author": self.author.to_json(),
            "rating": self.rating,
            "path": f"/zitate/{self.get_id_as_str()}",
        }

    def __str__(self) -> str:
        r"""
        Return the wrong quote.

        like: '»quote« - author'.
        """
        return f"»{self.quote}« - {self.author}"


def get_wrong_quotes(
    filter_fun: None | Callable[[WrongQuote], bool] = None,
    sort: bool = False,  # sorted by rating
    filter_real_quotes: bool = True,
    shuffle: bool = False,
) -> tuple[WrongQuote, ...]:
    """Get cached wrong quotes."""
    if shuffle and sort:
        raise ValueError("Sort and shuffle can't be both true.")
    wqs: Iterable[WrongQuote] = WRONG_QUOTES_CACHE.values()
    if filter_fun is not None:
        # pylint: disable=bad-builtin
        wqs = filter(filter_fun, wqs)
    if filter_real_quotes:
        # pylint: disable=bad-builtin
        wqs = filter(lambda wq: wq.quote.author.id != wq.author.id, wqs)
    if not (shuffle or sort):
        return tuple(wqs)
    wqs_list = list(wqs)  # shuffle or sort is True
    if shuffle:
        random.shuffle(wqs_list)
    if sort:
        wqs_list.sort(key=lambda wq: wq.rating, reverse=True)
    return tuple(wqs_list)


def get_quotes(
    filter_fun: None | Callable[[Quote], bool] = None,
    shuffle: bool = False,
) -> list[Quote]:
    """Get cached quotes."""
    quotes: list[Quote] = list(QUOTES_CACHE.values())
    if filter_fun is not None:
        quotes = [_q for _q in quotes if filter_fun(_q)]
    if shuffle:
        random.shuffle(quotes)
    return quotes


def get_authors(
    filter_fun: None | Callable[[Author], bool] = None,
    shuffle: bool = False,
) -> list[Author]:
    """Get cached authors."""
    authors: list[Author] = list(AUTHORS_CACHE.values())
    if filter_fun is not None:
        authors = [_a for _a in authors if filter_fun(_a)]
    if shuffle:
        random.shuffle(authors)
    return list(authors)


async def make_api_request(
    endpoint: str,
    args: str = "",
    method: Literal["GET", "POST"] = "GET",
    body: None | str = None,
) -> Any:  # list[dict[str, Any]] | dict[str, Any]:
    """Make API request and return the result as dict."""
    response = await AsyncHTTPClient().fetch(
        f"{API_URL}/{endpoint}?{args}",
        method=method,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=body,
        raise_error=False,
        ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
    )
    if response.code != 200:
        logger.error(
            "%s request to '%s/%s?%s' with body='%s' "
            "failed with code=%d and reason='%s'",
            method,
            API_URL,
            endpoint,
            args,
            body,
            response.code,
            response.reason,
        )
        raise HTTPError(
            400,
            reason=(
                f"{API_URL}/{endpoint} returned: "
                f"{response.code} {response.reason}"
            ),
        )
    return json.loads(response.body)


def get_author_updated_with(author_id: int, author_name: str) -> Author:
    """Get the author with the given id and the name."""
    author_name = author_name.strip()
    if not author_name:
        author_name = "None"
    author = AUTHORS_CACHE.setdefault(
        author_id,
        Author(author_id, author_name),
    )
    author.update_name(author_name)
    MAX_AUTHORS_ID[0] = max(MAX_AUTHORS_ID[0], author_id)
    return author


def parse_author(json_data: dict[str, Any]) -> Author:
    """Parse an author from JSON data."""
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


def parse_quote(json_data: dict[str, Any]) -> Quote:
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


def parse_wrong_quote(json_data: dict[str, Any]) -> WrongQuote:
    """Parse a quote."""
    id_tuple = (int(json_data["quote"]["id"]), int(json_data["author"]["id"]))
    rating = json_data["rating"]
    wrong_quote_id = int(json_data.get("id") or -1)
    wrong_quote = WRONG_QUOTES_CACHE.setdefault(
        id_tuple,
        WrongQuote(
            id=wrong_quote_id,
            quote=parse_quote(json_data["quote"]),
            author=parse_author(json_data["author"]),
            rating=rating,
        ),
    )
    # make sure the wrong quote is the correct one
    assert (wrong_quote.quote.id, wrong_quote.author.id) == id_tuple
    # update the data of the wrong quote
    if wrong_quote.rating != rating:
        wrong_quote.rating = rating
    if wrong_quote.id != wrong_quote_id:
        wrong_quote.id = wrong_quote_id
    return wrong_quote


def parse_list_of_quote_data(
    json_list: str | list[dict[str, Any]],
    parse_fun: Callable[[dict[str, Any]], QuotesObjBase],
) -> tuple[QuotesObjBase, ...]:
    """Parse a list of quote data."""
    if not json_list:
        return tuple()
    if isinstance(json_list, str):
        _json_list: list[dict[str, Any]] = json.loads(json_list)
    else:
        _json_list = json_list
    return tuple(parse_fun(json_data) for json_data in _json_list)


async def update_cache_periodically(
    app: tornado.web.Application,
    setup_redis_awaitable: None | Awaitable[Any] = None,
) -> None:
    """Start updating the cache every hour."""
    if setup_redis_awaitable:
        await setup_redis_awaitable
    redis: None | Redis = app.settings.get("REDIS")
    prefix: str = app.settings.get("REDIS_PREFIX", "")
    if redis:
        parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:wrongquotes"),
            parse_wrong_quote,
        )
        parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:quotes"),
            parse_quote,
        )
        parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:authors"),
            parse_author,
        )
    if redis and QUOTES_CACHE and AUTHORS_CACHE and WRONG_QUOTES_CACHE:
        last_update = await redis.get(f"{prefix}:cached-quote-data:last-update")
        if last_update:
            last_update_int = int(last_update)
            since_last_update = int(time.time()) - last_update_int
            if 0 <= since_last_update < 60 * 60:
                # wait until the last update is at least one hour old
                update_cache_in = 60 * 60 - since_last_update
                if not sys.flags.dev_mode and update_cache_in > 60:
                    # if in production mode update wrong quotes just to be sure
                    await update_cache(
                        app, update_quotes=False, update_authors=False
                    )
                logger.info(
                    "Next update of quotes cache in %d seconds",
                    update_cache_in,
                )
                await asyncio.sleep(update_cache_in)

    # pylint: disable=while-used
    while True:  # update the cache every hour
        await update_cache(app)
        await asyncio.sleep(60 * 60)


async def update_cache(  # noqa: C901  # pylint: disable=too-complex
    app: tornado.web.Application,
    update_wrong_quotes: bool = True,
    update_quotes: bool = True,
    update_authors: bool = True,
) -> None:
    """Fill the cache with all data from the API."""
    logger.info("Updating quotes cache...")
    redis: None | Redis = app.settings.get("REDIS")
    prefix: str = app.settings.get("REDIS_PREFIX", "")
    try:  # pylint: disable=too-many-try-statements

        if update_wrong_quotes:
            parse_list_of_quote_data(
                wq_data := await make_api_request("wrongquotes"),
                parse_wrong_quote,
            )
            if wq_data and redis:
                await redis.set(
                    f"{prefix}:cached-quote-data:wrongquotes",
                    json.dumps(wq_data, option=ORJSON_OPTIONS),
                )

        if update_quotes:
            parse_list_of_quote_data(
                quotes_data := await make_api_request("quotes"),
                parse_quote,
            )
            if quotes_data and redis:
                await redis.set(
                    f"{prefix}:cached-quote-data:quotes",
                    json.dumps(quotes_data, option=ORJSON_OPTIONS),
                )

        if update_authors:
            parse_list_of_quote_data(
                authors_data := await make_api_request("authors"),
                parse_author,
            )
            if authors_data and redis:
                await redis.set(
                    f"{prefix}:cached-quote-data:authors",
                    json.dumps(authors_data, option=ORJSON_OPTIONS),
                )

        if redis and update_wrong_quotes and update_quotes and update_authors:
            await redis.set(
                f"{prefix}:cached-quote-data:last-update",
                int(time.time()),
            )

    except Exception as exc:  # pylint: disable=broad-except
        logger.exception(exc)
        logger.error("Updating quotes cache failed.")
        apm: None | elasticapm.Client = app.settings.get("ELASTIC_APM_CLIENT")
        if apm:
            apm.capture_exception()
    else:
        logger.info("Updated quotes cache successfully.")


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
    quote_id: int, author_id: int, use_cache: bool = True
) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    wrong_quote = WRONG_QUOTES_CACHE.get((quote_id, author_id), None)

    if wrong_quote:
        if use_cache:
            return wrong_quote
        # do not use cache, so update the wrong quote data
        return await wrong_quote.fetch_new_data()
    # wrong quote not in cache
    if use_cache and quote_id in QUOTES_CACHE and author_id in AUTHORS_CACHE:
        # we don't need to request anything, as the wrong_quote probably has
        # no ratings just use the cached quote and author
        return WrongQuote(
            -1,
            QUOTES_CACHE[quote_id],
            AUTHORS_CACHE[author_id],
            0,
        )
    # request the wrong quote from the API
    result = await make_api_request(
        "wrongquotes",
        f"quote={quote_id}&author={author_id}&simulate=true",
    )
    if result:
        return parse_wrong_quote(result[0])

    raise HTTPError(404, reason="Falsches Zitat nicht gefunden.")


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
    if wrong_quote and wrong_quote.id != -1:
        return await wrong_quote.vote(vote, fast)
    # we don't know the wrong_quote_id, so we have to create the wrong_quote
    wrong_quote = parse_wrong_quote(
        await make_api_request(
            "wrongquotes",
            method="POST",
            body=(
                f"quote={quote_id}&author={author_id}&"
                f"contributed_by={contributed_by}"
            ),
        )
    )
    return await wrong_quote.vote(vote, fast=True)


class QuoteReadyCheckHandler(HTMLRequestHandler):
    """Class that checks if quotes have been loaded."""

    async def check_ready(self) -> None:
        """Fail if quotes aren't ready yet."""
        if not WRONG_QUOTES_CACHE:
            # should work in a few seconds, the quotes just haven't loaded yet
            self.set_header("Retry-After", "5")
            raise HTTPError(503, reason="Service available in a few seconds.")

    async def prepare(self) -> None:
        await super().prepare()
        if self.request.method != "OPTIONS":
            await self.check_ready()
