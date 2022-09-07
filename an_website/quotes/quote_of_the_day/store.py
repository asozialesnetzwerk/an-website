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

"""Stores that contain the ids of old quote of the day."""
from __future__ import annotations

import abc
from datetime import date, datetime
from typing import ClassVar, Final

from redis.asyncio import Redis
from tornado.web import HTTPError

from ... import EVENT_REDIS

QUOTE_COUNT_TO_SHOW_IN_FEED: Final[int] = 8


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
