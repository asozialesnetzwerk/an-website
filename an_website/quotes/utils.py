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

import abc
import asyncio
import contextlib
import logging
import multiprocessing.synchronize
import random
import sys
import time
from collections.abc import (
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import dataclass
from datetime import date
from multiprocessing import Value
from typing import Any, Final, Literal, cast
from urllib.parse import urlencode

import dill  # type: ignore[import-untyped]  # nosec: B403
import elasticapm
import orjson as json
import typed_stream
from redis.asyncio import Redis
from tornado.httpclient import AsyncHTTPClient
from tornado.web import Application, HTTPError
from UltraDict import UltraDict  # type: ignore[import-untyped]

from .. import (
    CA_BUNDLE_PATH,
    DIR as ROOT_DIR,
    EVENT_REDIS,
    EVENT_SHUTDOWN,
    NAME,
    ORJSON_OPTIONS,
    pytest_is_running,
)
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo, Permission, ratelimit

DIR: Final = ROOT_DIR / "quotes"

LOGGER: Final = logging.getLogger(__name__)

API_URL: Final[str] = "https://zitate.prapsschnalinen.de/api"


# pylint: disable-next=too-few-public-methods
class UltraDictType[K, V](MutableMapping[K, V], abc.ABC):
    """The type of the shared dictionaries."""

    lock: multiprocessing.synchronize.RLock


QUOTES_CACHE: Final[UltraDictType[int, Quote]] = UltraDict(
    buffer_size=1024**2, serializer=dill
)
AUTHORS_CACHE: Final[UltraDictType[int, Author]] = UltraDict(
    buffer_size=1024**2, serializer=dill
)
WRONG_QUOTES_CACHE: Final[UltraDictType[tuple[int, int], WrongQuote]] = (
    UltraDict(buffer_size=1024**2, serializer=dill)
)

MAX_QUOTES_ID = Value("Q", 0)
MAX_AUTHORS_ID = Value("Q", 0)


@dataclass(init=False, slots=True)
class QuotesObjBase(abc.ABC):
    """An object with an id."""

    id: int

    @abc.abstractmethod
    async def fetch_new_data(self) -> QuotesObjBase:
        """Fetch new data from the API."""
        raise NotImplementedError

    # pylint: disable=unused-argument
    def get_id_as_str(self, minify: bool = False) -> str:
        """Get the id of the object as a string."""
        return str(self.id)

    @abc.abstractmethod
    def get_path(self) -> str:
        """Return the path to the Object."""
        raise NotImplementedError


@dataclass(slots=True)
class Author(QuotesObjBase):
    """The author object with a name."""

    name: str
    # tuple(url_to_info, info_str, creation_date)
    info: None | tuple[str, None | str, date]

    def __str__(self) -> str:
        """Return the name of the author."""
        return self.name

    async def fetch_new_data(self) -> Author:
        """Fetch new data from the API."""
        return parse_author(
            await make_api_request(
                f"authors/{self.id}", entity_should_exist=True
            )
        )

    def get_path(self) -> str:
        """Return the path to the author info."""
        return f"/zitate/info/a/{self.id}"

    def to_json(self) -> dict[str, Any]:
        """Get the author as JSON."""
        return {
            "id": self.id,
            "name": str(self),
            "path": self.get_path(),
            "info": (
                {
                    "source": self.info[0],
                    "text": self.info[1],
                    "date": self.info[2].isoformat(),
                }
                if self.info
                else None
            ),
        }


@dataclass(slots=True)
class Quote(QuotesObjBase):
    """The quote object with a quote text and an author."""

    quote: str
    author_id: int

    def __str__(self) -> str:
        """Return the content of the quote."""
        return self.quote.strip()

    @property
    def author(self) -> Author:
        """Get the corresponding author object."""
        return AUTHORS_CACHE[self.author_id]

    async def fetch_new_data(self) -> Quote:
        """Fetch new data from the API."""
        return parse_quote(
            await make_api_request(
                f"quotes/{self.id}", entity_should_exist=True
            ),
            self,
        )

    def get_path(self) -> str:
        """Return the path to the quote info."""
        return f"/zitate/info/z/{self.id}"

    def to_json(self) -> dict[str, Any]:
        """Get the quote as JSON."""
        return {
            "id": self.id,
            "quote": str(self),
            "author": self.author.to_json(),
            "path": self.get_path(),
        }


@dataclass(slots=True)
class WrongQuote(QuotesObjBase):
    """The wrong quote object with a quote, an author and a rating."""

    quote_id: int
    author_id: int
    rating: int

    def __str__(self) -> str:
        r"""
        Return the wrong quote.

        like: '»quote« - author'.
        """
        return f"»{self.quote}« - {self.author}"

    @property
    def author(self) -> Author:
        """Get the corresponding author object."""
        return AUTHORS_CACHE[self.author_id]

    async def fetch_new_data(self) -> WrongQuote:
        """Fetch new data from the API."""
        if self.id == -1:
            api_data = await make_api_request(
                "wrongquotes",
                {
                    "quote": str(self.quote_id),
                    "simulate": "true",
                    "author": str(self.author_id),
                },
                entity_should_exist=True,
            )
            if api_data:
                api_data = api_data[0]
        else:
            api_data = await make_api_request(
                f"wrongquotes/{self.id}", entity_should_exist=True
            )
        if not api_data:
            return self
        return parse_wrong_quote(api_data, self)

    def get_id(self) -> tuple[int, int]:
        """
        Get the id of the quote and the author in a tuple.

        :return tuple(quote_id, author_id)
        """
        return self.quote_id, self.author_id

    def get_id_as_str(self, minify: bool = False) -> str:
        """
        Get the id of the wrong quote as a string.

        Format: quote_id-author_id
        """
        if minify and self.id != -1:
            return str(self.id)
        return f"{self.quote_id}-{self.author_id}"

    def get_path(self) -> str:
        """Return the path to the wrong quote."""
        return f"/zitate/{self.get_id_as_str()}"

    @property
    def quote(self) -> Quote:
        """Get the corresponding quote object."""
        return QUOTES_CACHE[self.quote_id]

    def to_json(self) -> dict[str, Any]:
        """Get the wrong quote as JSON."""
        return {
            "id": self.get_id_as_str(),
            "quote": self.quote.to_json(),
            "author": self.author.to_json(),
            "rating": self.rating,
            "path": self.get_path(),
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
                entity_should_exist=True,
            ),
            self,
        )


def get_wrong_quotes(
    filter_fun: None | Callable[[WrongQuote], bool] = None,
    *,
    sort: bool = False,  # sorted by rating
    filter_real_quotes: bool = True,
    shuffle: bool = False,
) -> Sequence[WrongQuote]:
    """Get cached wrong quotes."""
    if shuffle and sort:
        raise ValueError("Sort and shuffle can't be both true.")
    wqs: list[WrongQuote] = list(WRONG_QUOTES_CACHE.values())
    if filter_fun or filter_real_quotes:
        for i in reversed(range(len(wqs))):
            if (filter_fun and not filter_fun(wqs[i])) or (
                filter_real_quotes
                and wqs[i].quote.author_id == wqs[i].author_id
            ):
                del wqs[i]
    if shuffle:
        random.shuffle(wqs)
    elif sort:
        wqs.sort(key=lambda wq: wq.rating, reverse=True)
    return wqs


def get_quotes(
    filter_fun: None | Callable[[Quote], bool] = None,
    shuffle: bool = False,
) -> list[Quote]:
    """Get cached quotes."""
    quotes: list[Quote] = list(QUOTES_CACHE.values())
    if filter_fun:
        for i in reversed(range(len(quotes))):
            if not filter_fun(quotes[i]):
                del quotes[i]
    if shuffle:
        random.shuffle(quotes)
    return quotes


def get_authors(
    filter_fun: None | Callable[[Author], bool] = None,
    shuffle: bool = False,
) -> list[Author]:
    """Get cached authors."""
    authors: list[Author] = list(AUTHORS_CACHE.values())
    if filter_fun:
        for i in reversed(range(len(authors))):
            if not filter_fun(authors[i]):
                del authors[i]
    if shuffle:
        random.shuffle(authors)
    return authors


async def make_api_request(
    endpoint: str,
    args: Mapping[str, str] | None = None,
    *,
    entity_should_exist: bool,
    method: Literal["GET", "POST"] = "GET",
    body: None | Mapping[str, str] = None,
) -> Any:  # TODO: list[dict[str, Any]] | dict[str, Any]:
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
        ca_certs=CA_BUNDLE_PATH,
    )
    if response.code != 200:
        normed_response_code = (
            400
            if not entity_should_exist and response.code == 500
            else response.code
        )
        LOGGER.log(
            logging.ERROR if normed_response_code >= 500 else logging.WARNING,
            "%s request to %r with body=%r failed with code=%d and reason=%r",
            method,
            url,
            body_str,
            response.code,
            response.reason,
        )
        raise HTTPError(
            normed_response_code if normed_response_code in {400, 404} else 503,
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


def parse_author(json_data: Mapping[str, Any]) -> Author:
    """Parse an author from JSON data."""
    id_ = int(json_data["id"])
    name = fix_author_name(json_data["author"])

    with AUTHORS_CACHE.lock:
        author = AUTHORS_CACHE.get(id_)
        if author is None:
            # pylint: disable-next=too-many-function-args
            author = Author(id_, name, None)
            MAX_AUTHORS_ID.value = max(MAX_AUTHORS_ID.value, id_)
        elif author.name != name:
            author.name = name
            author.info = None  # reset info

        AUTHORS_CACHE[author.id] = author

    return author


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


def parse_quote(
    json_data: Mapping[str, Any], quote: None | Quote = None
) -> Quote:
    """Parse a quote from JSON data."""
    quote_id = int(json_data["id"])
    author = parse_author(json_data["author"])  # update author
    quote_str = fix_quote_str(json_data["quote"])

    with QUOTES_CACHE.lock:
        if quote is None:  # no quote supplied, try getting it from cache
            quote = QUOTES_CACHE.get(quote_id)
        if quote is None:  # new quote
            # pylint: disable=too-many-function-args
            quote = Quote(quote_id, quote_str, author.id)
            MAX_QUOTES_ID.value = max(MAX_QUOTES_ID.value, quote.id)
        else:  # quote was already saved
            quote.quote = quote_str
            quote.author_id = author.id

        QUOTES_CACHE[quote.id] = quote

    return quote


def parse_wrong_quote(
    json_data: Mapping[str, Any], wrong_quote: None | WrongQuote = None
) -> WrongQuote:
    """Parse a wrong quote and update the cache."""
    quote = parse_quote(json_data["quote"])
    author = parse_author(json_data["author"])

    id_tuple = (quote.id, author.id)
    rating = json_data["rating"]
    wrong_quote_id = int(json_data.get("id") or -1)

    if wrong_quote is None:
        with WRONG_QUOTES_CACHE.lock:
            wrong_quote = WRONG_QUOTES_CACHE.get(id_tuple)
            if wrong_quote is None:
                wrong_quote = (
                    WrongQuote(  # pylint: disable=unexpected-keyword-arg
                        id=wrong_quote_id,
                        quote_id=quote.id,
                        author_id=author.id,
                        rating=rating,
                    )
                )
                WRONG_QUOTES_CACHE[id_tuple] = wrong_quote
                return wrong_quote

    # make sure the wrong quote is the correct one
    if (wrong_quote.quote_id, wrong_quote.author_id) != id_tuple:
        raise HTTPError(reason="ERROR: -41")

    # update the data of the wrong quote
    if wrong_quote.rating != rating:
        wrong_quote.rating = rating
    if wrong_quote.id != wrong_quote_id:
        wrong_quote.id = wrong_quote_id

    WRONG_QUOTES_CACHE[id_tuple] = wrong_quote

    return wrong_quote


async def parse_list_of_quote_data(
    json_list: str | Iterable[Mapping[str, Any]],
    parse_fun: Callable[[Mapping[str, Any]], QuotesObjBase],
) -> tuple[QuotesObjBase, ...]:
    """Parse a list of quote data."""
    if not json_list:
        return ()
    if isinstance(json_list, str):
        json_list = cast(list[dict[str, Any]], json.loads(json_list))
    return_list = []
    for json_data in json_list:
        _ = parse_fun(json_data)
        await asyncio.sleep(0)
        return_list.append(_)
    return tuple(return_list)


async def update_cache_periodically(
    app: Application, worker: int | None
) -> None:
    """Start updating the cache every hour."""
    # pylint: disable=too-complex, too-many-branches
    if "/troet" in typed_stream.Stream(
        cast(Iterable[ModuleInfo], app.settings.get("MODULE_INFOS", ()))
    ).map(lambda m: m.path):
        app.settings["SHOW_SHARING_ON_MASTODON"] = True
    if worker:
        return
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(EVENT_REDIS.wait(), 5)
    redis: Redis[str] = cast("Redis[str]", app.settings.get("REDIS"))
    prefix: str = app.settings.get("REDIS_PREFIX", NAME).removesuffix("-dev")
    apm: None | elasticapm.Client
    if EVENT_REDIS.is_set():  # pylint: disable=too-many-nested-blocks
        await parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:authors"),  # type: ignore[arg-type]  # noqa: B950
            parse_author,
        )
        await parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:quotes"),  # type: ignore[arg-type]  # noqa: B950
            parse_quote,
        )
        await parse_list_of_quote_data(
            await redis.get(f"{prefix}:cached-quote-data:wrongquotes"),  # type: ignore[arg-type]  # noqa: B950
            parse_wrong_quote,
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
        await parse_list_of_quote_data(
            wq_data := await make_api_request(
                "wrongquotes", entity_should_exist=True
            ),
            parse_wrong_quote,
        )
        if wq_data and redis_available:
            await redis.setex(
                f"{prefix}:cached-quote-data:wrongquotes",
                60 * 60 * 24 * 30,
                json.dumps(wq_data, option=ORJSON_OPTIONS),
            )

    if update_quotes:
        await parse_list_of_quote_data(
            quotes_data := await make_api_request(
                "quotes", entity_should_exist=True
            ),
            parse_quote,
        )
        if quotes_data and redis_available:
            await redis.setex(
                f"{prefix}:cached-quote-data:quotes",
                60 * 60 * 24 * 30,
                json.dumps(quotes_data, option=ORJSON_OPTIONS),
            )

    if update_authors:
        await parse_list_of_quote_data(
            authors_data := await make_api_request(
                "authors", entity_should_exist=True
            ),
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
    author = AUTHORS_CACHE.get(author_id)
    if author is not None:
        return author
    return parse_author(
        await make_api_request(
            f"authors/{author_id}", entity_should_exist=False
        )
    )


async def get_quote_by_id(quote_id: int) -> Quote:
    """Get a quote by its id."""
    quote = QUOTES_CACHE.get(quote_id)
    if quote is not None:
        return quote
    return parse_quote(
        await make_api_request(f"quotes/{quote_id}", entity_should_exist=False)
    )


async def get_wrong_quote(
    quote_id: int, author_id: int, use_cache: bool = True
) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    wrong_quote = WRONG_QUOTES_CACHE.get((quote_id, author_id))
    if wrong_quote:
        if use_cache:
            return wrong_quote
        # do not use cache, so update the wrong quote data
        return await wrong_quote.fetch_new_data()
    # wrong quote not in cache
    if use_cache and quote_id in QUOTES_CACHE and author_id in AUTHORS_CACHE:
        # we don't need to request anything, as the wrong_quote probably has
        # no ratings just use the cached quote and author
        # pylint: disable-next=too-many-function-args
        return WrongQuote(-1, quote_id, author_id, 0)
    # request the wrong quote from the API
    result = await make_api_request(
        "wrongquotes",
        {
            "quote": str(quote_id),
            "simulate": "true",
            "author": str(author_id),
        },
        entity_should_exist=False,
    )
    if result:
        return parse_wrong_quote(result[0])

    raise HTTPError(404, reason="Falsches Zitat nicht gefunden")


async def get_rating_by_id(quote_id: int, author_id: int) -> int:
    """Get the rating of a wrong quote."""
    return (await get_wrong_quote(quote_id, author_id)).rating


def get_random_quote_id() -> int:
    """Get random quote id."""
    return random.randint(1, MAX_QUOTES_ID.value)  # nosec: B311


def get_random_author_id() -> int:
    """Get random author id."""
    return random.randint(1, MAX_AUTHORS_ID.value)  # nosec: B311


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
    wrong_quote = WRONG_QUOTES_CACHE.get((quote_id, author_id))
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
            entity_should_exist=False,
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

        if (  # pylint: disable=too-many-boolean-expressions
            self.settings.get("RATELIMITS")
            and self.request.method not in {"HEAD", "OPTIONS"}
            and not self.is_authorized(Permission.RATELIMITS)
            and not self.crawler
            and (
                self.request.path.endswith(".xlsx")
                or self.content_type == "application/vnd.ms-excel"
            )
        ):
            if self.settings.get("UNDER_ATTACK") or not EVENT_REDIS.is_set():
                raise HTTPError(503)

            ratelimited, headers = await ratelimit(
                self.redis,
                self.redis_prefix,
                str(self.request.remote_ip),
                bucket="quotes:image:xlsx",
                max_burst=4,
                count_per_period=1,
                period=60,
                tokens=1 if self.request.method != "HEAD" else 0,
            )

            for header, value in headers.items():
                self.set_header(header, value)

            if ratelimited:
                if self.now.date() == date(self.now.year, 4, 20):
                    self.set_status(420)
                    self.write_error(420)
                else:
                    self.set_status(429)
                    self.write_error(429)
