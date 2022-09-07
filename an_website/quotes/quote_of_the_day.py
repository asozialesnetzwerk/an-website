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

"""Get a random quote for a given day."""

from __future__ import annotations

import abc
import dataclasses
import email.utils
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, ClassVar, Final

from redis.asyncio import Redis
from tornado.web import HTTPError

from .. import EVENT_REDIS
from ..utils.request_handler import APIRequestHandler
from .utils import (
    QuoteReadyCheckHandler,
    WrongQuote,
    get_wrong_quote,
    get_wrong_quotes,
)

LOGGER: Final = logging.getLogger(__name__)
QUOTE_COUNT_TO_SHOW_IN_FEED: Final[int] = 8


@dataclasses.dataclass
class QuoteOfTheDayData:
    """The class representing data for the quote of the day."""

    __slots__ = ("date", "wrong_quote", "url_without_path")
    date: date
    wrong_quote: WrongQuote
    url_without_path: str

    def get_date_for_rss(self) -> str:
        """Get the date as specified in RFC 2822."""
        return email.utils.format_datetime(
            datetime(
                year=self.date.year,
                month=self.date.month,
                day=self.date.day,
                tzinfo=timezone.utc,
            ),
            True,
        )

    def get_quote_as_str(self, new_line_char: str = "\n") -> str:
        """Get the quote as a string with new line."""
        return (
            f"»{self.wrong_quote.quote}«{new_line_char}"
            f"- {self.wrong_quote.author}"
        )

    def get_quote_image_url(self) -> str:
        """Get the URL of the image of the quote."""
        return self.get_quote_url() + ".gif"

    def get_quote_url(self) -> str:
        """Get the URL of the quote."""
        return (
            f"{self.url_without_path}/zitate/{self.wrong_quote.get_id_as_str()}"
        )

    def get_title(self) -> str:
        """Get the title for the quote of the day."""
        return f"Das Zitat des Tages vom {self.date:%d. %m. %Y}"

    def to_json(self) -> dict[str, Any]:
        """Get the quote of the day as JSON."""
        return {
            "date": self.date.isoformat(),
            "wrong_quote": self.wrong_quote.to_json(),
            "url": self.get_quote_url(),
            "image": self.get_quote_image_url(),
        }


class QuoteOfTheDayStore(abc.ABC):
    """The class representing the store for the quote of the day."""

    __slots__ = ()

    CACHE: ClassVar[dict[date, tuple[int, int]]] = {}

    @classmethod
    def _get_quote_id_from_cache(cls, date_: date) -> None | tuple[int, int]:
        """Get a quote_id from the cache if it is present."""
        return cls.CACHE.get(date_)

    @classmethod
    def _populate_cache(cls, date_: date, quote_id: tuple[int, int]) -> None:
        """Populate the cache for the quote of today."""
        today = datetime.utcnow().date()
        # old entries are rarely used, they don't need to be cached
        if (today - date_).days > QUOTE_COUNT_TO_SHOW_IN_FEED:
            cls.CACHE[date_] = quote_id

        for key in tuple(cls.CACHE):
            # remove old entries from cache to save memory
            if (today - key).days > QUOTE_COUNT_TO_SHOW_IN_FEED:
                del cls.CACHE[key]

    @abc.abstractmethod
    async def get_quote_id_by_date(self, date_: date) -> tuple[int, int] | None:
        """Get the quote ID for the given date."""
        raise NotImplementedError

    @abc.abstractmethod
    async def has_quote_been_used(self, quote_id: tuple[int, int]) -> bool:
        """Check if the quote has been used already."""
        raise NotImplementedError

    @abc.abstractmethod
    async def set_quote_id_by_date(
        self, date_: date, quote_id: tuple[int, int]
    ) -> None:
        """Set the quote ID for the given date."""
        raise NotImplementedError

    @abc.abstractmethod
    async def set_quote_to_used(self, quote_id: tuple[int, int]) -> None:
        """Set the quote as used."""
        raise NotImplementedError


class RedisQuoteOfTheDayStore(QuoteOfTheDayStore):
    """A quote of the day store that stores the quote of the day in redis."""

    __slots__ = ("redis", "redis_prefix")

    redis_prefix: str
    redis: Redis[str]

    def __init__(self, redis: Redis[str], redis_prefix: str) -> None:
        """Initialize the redis quote of the day store."""
        self.redis = redis
        self.redis_prefix = redis_prefix

    async def get_quote_id_by_date(self, date_: date) -> tuple[int, int] | None:
        """Get the quote ID for the given date."""
        if date_ in self.CACHE:
            return self.CACHE[date_]
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)
        wq_id = await self.redis.get(self.get_redis_quote_date_key(date_))
        if not wq_id:
            return None
        quote, author = wq_id.split("-")
        quote_id = int(quote), int(author)
        self._populate_cache(date_, quote_id)
        return quote_id

    def get_redis_quote_date_key(self, wq_date: date) -> str:
        """Get the Redis key for getting quotes by date."""
        return f"{self.redis_prefix}:quote-of-the-day:by-date:{wq_date.isoformat()}"

    def get_redis_used_key(self, wq_id: tuple[int, int]) -> str:
        """Get the Redis used key."""
        str_id = "-".join(map(str, wq_id))  # pylint: disable=bad-builtin
        return f"{self.redis_prefix}:quote-of-the-day:used:{str_id}"

    async def has_quote_been_used(self, quote_id: tuple[int, int]) -> bool:
        """Check if the quote has been used already."""
        if quote_id in self.CACHE.values():
            return True
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)
        return bool(await self.redis.get(self.get_redis_used_key(quote_id)))

    async def set_quote_id_by_date(
        self, date_: date, quote_id: tuple[int, int]
    ) -> None:
        """Set the quote ID for the given date."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)
        await self.redis.setex(
            self.get_redis_quote_date_key(date_),
            60 * 60 * 24 * 420,  # TTL
            "-".join(map(str, quote_id)),  # pylint: disable=bad-builtin
        )
        self._populate_cache(date_, quote_id)

    async def set_quote_to_used(self, quote_id: tuple[int, int]) -> None:
        """Set the quote as used."""
        if not EVENT_REDIS.is_set():
            return

        await self.redis.setex(
            self.get_redis_used_key(quote_id),
            #  we have over 720 funny wrong quotes, so 420 should be ok
            60 * 60 * 24 * 420,  # TTL
            1,  # True
        )


class QuoteOfTheDayBaseHandler(QuoteReadyCheckHandler):
    """The base request handler for the quote of the day."""

    async def get_quote_by_date(
        self, wq_date: date | str
    ) -> None | QuoteOfTheDayData:
        """Get the quote of the date if one was saved."""
        if isinstance(wq_date, str):
            wq_date = date.fromisoformat(wq_date)

        wq_id = await self.qod_store.get_quote_id_by_date(wq_date)
        if not wq_id:
            return None
        wrong_quote = await get_wrong_quote(*wq_id)
        if not wrong_quote:
            return None
        return QuoteOfTheDayData(
            wq_date, wrong_quote, self.get_scheme_and_netloc()
        )

    async def get_quote_of_today(self) -> None | QuoteOfTheDayData:
        """Get the quote for today."""
        today = datetime.utcnow().date()
        quote_data = await self.get_quote_by_date(today)
        if quote_data:  # if was saved already
            return quote_data
        quotes: tuple[WrongQuote, ...] = get_wrong_quotes(
            lambda wq: wq.rating > 1, shuffle=True
        )
        if not quotes:
            LOGGER.error("No quotes available")
            return None
        for quote in quotes:
            if await self.qod_store.has_quote_been_used(quote.get_id()):
                continue
            wq_id = quote.get_id()
            await self.qod_store.set_quote_to_used(wq_id)
            await self.qod_store.set_quote_id_by_date(today, wq_id)
            return QuoteOfTheDayData(today, quote, self.get_scheme_and_netloc())
        LOGGER.critical("Failed to generate a new quote of the day")
        return None

    def get_scheme_and_netloc(self) -> str:
        """Get the beginning of the URL."""
        return f"{self.request.protocol}://{self.request.host}"

    @property
    def qod_store(self) -> QuoteOfTheDayStore:
        """Get the store used to storing the quote of the day."""
        return RedisQuoteOfTheDayStore(self.redis, self.redis_prefix)


class QuoteOfTheDayRss(QuoteOfTheDayBaseHandler):
    """The request handler for the quote of the day RSS feed."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "application/rss+xml",
        "application/xml",
    )
    IS_NOT_HTML: ClassVar[bool] = True

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        if head:
            return
        today = datetime.utcnow().date()
        quotes = (
            await self.get_quote_of_today(),
            *[
                await self.get_quote_by_date(today - timedelta(days=i))
                for i in range(1, QUOTE_COUNT_TO_SHOW_IN_FEED)
            ],
        )
        await self.render(
            "rss/quote_of_the_day.xml",
            quotes=tuple(q for q in quotes if q),
        )


class QuoteOfTheDayAPI(APIRequestHandler, QuoteOfTheDayBaseHandler):
    """Handler for the JSON API that returns the quote of the day."""

    async def get(
        self,
        date_str: None | str = None,
        *,
        head: bool = False,  # pylint: disable=unused-argument
    ) -> None:
        """Handle GET requests."""
        quote_data = await (
            self.get_quote_by_date(date_str)
            if date_str
            else self.get_quote_of_today()
        )

        if not quote_data:
            raise HTTPError(404 if date_str else 503)

        if self.request.path.endswith("/full"):
            return await self.finish(quote_data.to_json())

        wrong_quote = quote_data.wrong_quote
        await self.finish_dict(
            date=quote_data.date.isoformat(),
            url=quote_data.get_quote_url(),
            id=wrong_quote.get_id_as_str(),
            quote=str(wrong_quote.quote),
            author=str(wrong_quote.author),
            rating=wrong_quote.rating,
        )


class QuoteOfTheDayRedirect(QuoteOfTheDayBaseHandler):
    """Redirect to the quote of the day."""

    async def get(
        self,
        date_str: None | str = None,
        *,
        head: bool = False,  # pylint: disable=unused-argument
    ) -> None:
        """Handle GET requests."""
        wrong_quote_data = await (
            self.get_quote_by_date(date_str)
            if date_str
            else self.get_quote_of_today()
        )

        if not wrong_quote_data:
            raise HTTPError(404 if date_str else 503)

        self.redirect(
            self.fix_url(
                wrong_quote_data.get_quote_url(),
            ),
            False,
        )
