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
import contextlib
import logging
import os
import random
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from multiprocessing import Value
from typing import Any, Final, Literal, cast
from urllib.parse import urlencode

import elasticapm  # type: ignore[import]
import orjson as json
from redis.asyncio import Redis
from tornado.httpclient import AsyncHTTPClient
from tornado.web import Application, HTTPError
from UltraDict import UltraDict  # type: ignore[import]

from .. import DIR as ROOT_DIR
from .. import (
    EVENT_REDIS,
    EVENT_SHUTDOWN,
    NAME,
    ORJSON_OPTIONS,
    pytest_is_running,
)
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import emojify

DIR: Final = os.path.dirname(__file__)

LOGGER: Final = logging.getLogger(__name__)

API_URL: Final[str] = "https://zitate.prapsschnalinen.de/api"

QUOTES_CACHE: Final[dict[int, Quote]] = UltraDict(buffer_size=1024**2)
AUTHORS_CACHE: Final[dict[int, Author]] = UltraDict(buffer_size=1024**2)
WRONG_QUOTES_CACHE: Final[dict[tuple[int, int], WrongQuote]] = UltraDict(
    buffer_size=1024**2
)

MAX_QUOTES_ID = Value("Q", 0)
MAX_AUTHORS_ID = Value("Q", 0)


@dataclass(init=False, slots=True)
class QuotesObjBase:
    """An object with an id."""

    id: int  # pylint: disable=invalid-name

    async def fetch_new_data(self) -> QuotesObjBase:
        """Fetch new data from the API."""
        raise NotImplementedError

    # pylint: disable=unused-argument
    def get_id_as_str(self, minify: bool = False) -> str:
        """Get the id of the object as a string."""
        return str(self.id)


@dataclass(slots=True)
class Author(QuotesObjBase):
    """The author object with a name."""

    name: str
    # tuple(url_to_info, info_str, creation_date)
    info: None | tuple[str, None | str, date]

    def __str__(self) -> str:
        """Return the name of the author."""
        return (
            emojify(self.name.strip())
            if (now := datetime.utcnow()).day == 1 and now.month == 4
            else self.name.strip()
        )

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

    def update_name(self, name: str) -> None:
        """Update author data with another author."""
        name = fix_author_name(name)
        if self.name != name:
            # name changed -> info should change too
            self.info = None
            self.name = name


@dataclass(slots=True)
class Quote(QuotesObjBase):
    """The quote object with a quote text and an author."""

    quote: str
    author: Author

    def __str__(self) -> str:
        """Return the content of the quote."""
        return (
            emojify(self.quote.strip())
            if (now := datetime.utcnow()).day == 1 and now.month == 4
            else self.quote.strip()
        )

    async def fetch_new_data(self) -> Quote:
        """Fetch new data from the API."""
        return parse_quote(await make_api_request(f"quotes/{self.id}"), self)

    def to_json(self) -> dict[str, Any]:
        """Get the quote as JSON."""
        return {
            "id": self.id,
            "quote": str(self),
            "author": self.author.to_json(),
            "path": f"/zitate/info/z/{self.id}",
        }

    def update_quote(
        self, quote: str, author_id: int, author_name: str
    ) -> None:
        """Update quote data with new data."""
        self.quote = fix_quote_str(quote)
        if self.author.id == author_id:
            self.author.update_name(author_name)
            return
        self.author = get_author_updated_with(author_id, author_name)


@dataclass(slots=True)
class WrongQuote(QuotesObjBase):
    """The wrong quote object with a quote, an author and a rating."""

    quote: Quote
    author: Author
    rating: int

    def __str__(self) -> str:
        r"""
        Return the wrong quote.

        like: '»quote« - author'.
        """
        return f"»{self.quote}« - {self.author}"

    async def fetch_new_data(self) -> WrongQuote:
        """Fetch new data from the API."""
        if self.id == -1:
            api_data = await make_api_request(
                "wrongquotes",
                {
                    "quote": str(self.quote.id),
                    "simulate": "true",
                    "author": str(self.author.id),
                },
            )
            if api_data:
                api_data = api_data[0]
        else:
            api_data = await make_api_request(f"wrongquotes/{self.id}")
        if not api_data:
            return self
        return parse_wrong_quote(api_data, self)

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

    def to_json(self) -> dict[str, Any]:
        """Get the wrong quote as JSON."""
        return {
            "id": self.get_id_as_str(),
            "quote": self.quote.to_json(),
            "author": self.author.to_json(),
            "rating": self.rating,
            "path": f"/zitate/{self.get_id_as_str()}",
        }

    async def vote(
        # pylint: disable=unused-argument
        self,
        vote: Literal[-1, 1],
        lazy: bool = False,
    ) -> WrongQuote:
        """Vote for the wrong quote."""
        if self.id == -1:
            raise ValueError("Can't vote for a not existing quote.")
        # if lazy:  # simulate the vote and do the actual voting later
        #     self.rating += vote
        #     asyncio.get_running_loop().call_soon_threadsafe(
        #         self.vote,
        #         vote,
        #     )
        #     return self
        # do the voting
        return parse_wrong_quote(
            await make_api_request(
                f"wrongquotes/{self.id}",
                method="POST",
                body={"vote": str(vote)},
            ),
            self,
        )


def get_wrong_quotes(
    filter_fun: None | Callable[[WrongQuote], bool] = None,
    *,
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
    args: dict[str, str] | None = None,
    *,
    method: Literal["GET", "POST"] = "GET",
    body: None | dict[str, str] = None,
) -> Any:  # list[dict[str, Any]] | dict[str, Any]:
    """Make API request and return the result as dict."""
    if pytest_is_running():
        return None
    query = f"?{urlencode(args)}" if args else ""
    url = f"{API_URL}/{endpoint}{query}"
    body_str = urlencode(body) if body else body
    response = await AsyncHTTPClient().fetch(
        url,
        method=method,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=body_str,
        raise_error=False,
        ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
    )
    if response.code != 200:
        LOGGER.warning(
            "%s request to %r with body=%r failed with code=%d and reason=%r",
            method,
            url,
            body_str,
            response.code,
            response.reason,
        )
        raise HTTPError(
            400
            if response.code == 500
            else (404 if response.code == 404 else 503),
            reason=(
                f"{API_URL}/{endpoint} returned: "
                f"{response.code} {response.reason}"
            ),
        )
    return json.loads(response.body)


def fix_author_name(name: str) -> str:
    """Fix common mistakes in authors."""
    if len(name) > 2 and name.startswith("(") and name.endswith(")"):
        # remove () from author name, that shouldn't be there
        name = name[1:-1]
    return name.strip()


def get_author_updated_with(author_id: int, name: str) -> Author:
    """Get the author with the given id and the name."""
    name = fix_author_name(name)
    if not name:
        name = "None"

    author = AUTHORS_CACHE.get(author_id)
    if author is None:  # author not in cache, create new one
        author = Author(author_id, name, None)
        MAX_AUTHORS_ID.value = max(  # type: ignore[attr-defined]
            MAX_AUTHORS_ID.value, author_id  # type: ignore[attr-defined]
        )
    else:  # update to make sure cache is correct
        author.update_name(name)

    AUTHORS_CACHE[author.id] = author

    return author


def parse_author(json_data: dict[str, Any]) -> Author:
    """Parse an author from JSON data."""
    return get_author_updated_with(int(json_data["id"]), json_data["author"])


def fix_quote_str(quote_str: str) -> str:
    """Fix common mistakes in quotes."""
    if (
        len(quote_str) > 2
        and quote_str.startswith(('"', "„", "“"))
        and quote_str.endswith(('"', "“", "”"))
    ):
        # remove quotation marks from quote, that shouldn't be there
        quote_str = quote_str[1:-1]

    return quote_str.strip()


def parse_quote(json_data: dict[str, Any], quote: None | Quote = None) -> Quote:
    """Parse a quote from JSON data."""
    quote_id = int(json_data["id"])
    author = parse_author(json_data["author"])  # update author
    quote_str = fix_quote_str(json_data["quote"])

    if quote is None:  # no quote supplied, try getting it from cache
        quote = QUOTES_CACHE.get(quote_id)
    if quote is None:  # new quote
        quote = Quote(quote_id, quote_str, author)
        MAX_QUOTES_ID.value = max(  # type: ignore[attr-defined]
            MAX_QUOTES_ID.value, quote.id  # type: ignore[attr-defined]
        )
    else:  # quote was already saved
        quote.update_quote(quote_str, author.id, author.name)

    QUOTES_CACHE[quote.id] = quote

    return quote


def parse_wrong_quote(
    json_data: dict[str, Any], wrong_quote: None | WrongQuote = None
) -> WrongQuote:
    """Parse a wrong quote and update the cache."""
    quote = parse_quote(json_data["quote"])
    author = parse_author(json_data["author"])

    id_tuple = (quote.id, author.id)
    rating = json_data["rating"]
    wrong_quote_id = int(json_data.get("id") or -1)

    if wrong_quote is None:
        wrong_quote = WRONG_QUOTES_CACHE.get(id_tuple)
        if wrong_quote is None:
            wrong_quote = WrongQuote(
                id=wrong_quote_id,
                quote=quote,
                author=author,
                rating=rating,
            )

    # make sure the wrong quote is the correct one
    if (wrong_quote.quote.id, wrong_quote.author.id) != id_tuple:
        raise HTTPError(reason="ERROR: -41")

    wrong_quote.quote = quote
    wrong_quote.author = author

    # update the data of the wrong quote
    if wrong_quote.rating != rating:
        wrong_quote.rating = rating
    if wrong_quote.id != wrong_quote_id:
        wrong_quote.id = wrong_quote_id

    WRONG_QUOTES_CACHE[id_tuple] = wrong_quote

    return wrong_quote


def parse_list_of_quote_data(
    json_list: str | list[dict[str, Any]],
    parse_fun: Callable[[dict[str, Any]], QuotesObjBase],
) -> tuple[QuotesObjBase, ...]:
    """Parse a list of quote data."""
    if not json_list:
        return ()
    if isinstance(json_list, str):
        _json_list: list[dict[str, Any]] = json.loads(json_list)
    else:
        _json_list = json_list
    return tuple(parse_fun(json_data) for json_data in _json_list)


async def update_cache_periodically(app: Application) -> None:  # noqa: C901
    """Start updating the cache every hour."""
    # pylint: disable=too-complex
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(EVENT_REDIS.wait(), 5)
    redis: Redis[str] = cast("Redis[str]", app.settings.get("REDIS"))
    prefix: str = app.settings.get("REDIS_PREFIX", NAME).removesuffix("-dev")
    apm: None | elasticapm.Client
    if EVENT_REDIS.is_set():  # pylint: disable=too-many-nested-blocks
        parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:wrongquotes"),  # type: ignore[arg-type]  # noqa: B950  # pylint: disable=line-too-long, useless-suppression
            parse_wrong_quote,
        )
        parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:quotes"),  # type: ignore[arg-type]  # noqa: B950  # pylint: disable=line-too-long, useless-suppression
            parse_quote,
        )
        parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:authors"),  # type: ignore[arg-type]  # noqa: B950  # pylint: disable=line-too-long, useless-suppression
            parse_author,
        )
        if QUOTES_CACHE and AUTHORS_CACHE and WRONG_QUOTES_CACHE:
            last_update = await redis.get(
                f"{prefix}:cached-quote-data:last-update"
            )
            if last_update:
                last_update_int = int(last_update)
                since_last_update = int(time.time()) - last_update_int
                if 0 <= since_last_update < 60 * 60:
                    # wait until the last update is at least one hour old
                    update_cache_in = 60 * 60 - since_last_update
                    if not sys.flags.dev_mode and update_cache_in > 60:
                        # if in production mode update wrong quotes just to be sure
                        try:
                            await update_cache(
                                app, update_quotes=False, update_authors=False
                            )
                        except Exception:  # pylint: disable=broad-except
                            LOGGER.exception("Updating quotes cache failed")
                            apm = app.settings.get("ELASTIC_APM", {}).get(
                                "CLIENT"
                            )
                            if apm:
                                apm.capture_exception()
                        else:
                            LOGGER.info("Updated quotes cache successfully")
                    LOGGER.info(
                        "Next update of quotes cache in %d seconds",
                        update_cache_in,
                    )
                    await asyncio.sleep(update_cache_in)

    # update the cache every hour
    failed = 0
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        try:
            await update_cache(app)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Updating quotes cache failed")
            if apm := app.settings.get("ELASTIC_APM", {}).get("CLIENT"):
                apm.capture_exception()
            failed += 1
            await asyncio.sleep(pow(min(failed * 2, 60), 2))  # 4,16,...,60*60
        else:
            LOGGER.info("Updated quotes cache successfully")
            failed = 0
            await asyncio.sleep(60 * 60)


async def update_cache(
    app: Application,
    update_wrong_quotes: bool = True,
    update_quotes: bool = True,
    update_authors: bool = True,
) -> None:
    """Fill the cache with all data from the API."""
    LOGGER.info("Updating quotes cache")
    redis: Redis[str] = cast("Redis[str]", app.settings.get("REDIS"))
    prefix: str = app.settings.get("REDIS_PREFIX", NAME).removesuffix("-dev")
    redis_available = EVENT_REDIS.is_set()

    if update_wrong_quotes:
        parse_list_of_quote_data(
            wq_data := await make_api_request("wrongquotes"),
            parse_wrong_quote,
        )
        if wq_data and redis_available:
            await redis.setex(
                f"{prefix}:cached-quote-data:wrongquotes",
                60 * 60 * 24 * 30,
                json.dumps(wq_data, option=ORJSON_OPTIONS),
            )

    if update_quotes:
        parse_list_of_quote_data(
            quotes_data := await make_api_request("quotes"),
            parse_quote,
        )
        if quotes_data and redis_available:
            await redis.setex(
                f"{prefix}:cached-quote-data:quotes",
                60 * 60 * 24 * 30,
                json.dumps(quotes_data, option=ORJSON_OPTIONS),
            )

    if update_authors:
        parse_list_of_quote_data(
            authors_data := await make_api_request("authors"),
            parse_author,
        )
        if authors_data and redis_available:
            await redis.setex(
                f"{prefix}:cached-quote-data:authors",
                60 * 60 * 24 * 30,
                json.dumps(authors_data, option=ORJSON_OPTIONS),
            )

    if (
        redis_available
        and update_wrong_quotes
        and update_quotes
        and update_authors
    ):
        await redis.setex(
            f"{prefix}:cached-quote-data:last-update",
            60 * 60 * 24 * 30,
            int(time.time()),
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
        {
            "quote": str(quote_id),
            "simulate": "true",
            "author": str(author_id),
        },
    )
    if result:
        return parse_wrong_quote(result[0])

    raise HTTPError(404, reason="Falsches Zitat nicht gefunden")


async def get_rating_by_id(quote_id: int, author_id: int) -> int:
    """Get the rating of a wrong quote."""
    return (await get_wrong_quote(quote_id, author_id)).rating


def get_random_quote_id() -> int:
    """Get random quote id."""
    return random.randint(  # nosec: B311
        1, MAX_QUOTES_ID.value  # type: ignore[attr-defined]
    )


def get_random_author_id() -> int:
    """Get random author id."""
    return random.randint(  # nosec: B311
        1, MAX_AUTHORS_ID.value  # type: ignore[attr-defined]
    )


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
            body={
                "quote": str(quote_id),
                "author": str(author_id),
                "contributed_by": contributed_by,
            },
        )
    )
    return await wrong_quote.vote(vote, lazy=True)


class QuoteReadyCheckHandler(HTMLRequestHandler):
    """Class that checks if quotes have been loaded."""

    async def check_ready(self) -> None:
        """Fail if quotes aren't ready yet."""
        if not WRONG_QUOTES_CACHE:
            # should work in a few seconds, the quotes just haven't loaded yet
            self.set_header("Retry-After", "5")
            raise HTTPError(503, reason="Service available in a few seconds")

    async def prepare(self) -> None:  # noqa: D102
        await super().prepare()
        if self.request.method != "OPTIONS":
            await self.check_ready()
