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

import email.utils
import random
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from ..utils.utils import ModuleInfo
from . import (
    WRONG_QUOTES_CACHE,
    QuoteReadyCheckRequestHandler,
    WrongQuote,
    get_wrong_quotes,
)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/zitat-des-tages/feed/", QuoteOfTheDayRss),),
        name="Falsche Zitate",
        description="Ein RSS-Feed mit dem Zitat des Tages.",
        path="/zitat-des-tages/feed/",
        keywords=(
            "Zitate",
            "Witzig",
            "Känguru",
        ),
        hidden=True,
    )


class QuoteOfTheDayRss(QuoteReadyCheckRequestHandler):
    """The base request handler for the quotes package."""

    async def get(self):
        """Handle GET requests."""
        _today_date = datetime.now(tz=timezone.utc).date()
        today = datetime(
            year=_today_date.year,
            month=_today_date.month,
            day=_today_date.day,
            tzinfo=timezone.utc,
        )
        quote = await self.get_quote_of_today()
        q_url = (
            f"{self.get_url_without_path()}/zitate/{quote.get_id_as_str()}/"
        )
        quotes: list[tuple[str, str, WrongQuote]] = [
            (email.utils.format_datetime(today), q_url, quote)
        ]
        for _i in range(1, 5):
            _date = today - timedelta(days=_i)
            _q = await self.get_quote_by_date(_date)
            print(_date, _q)
            if _q:
                quotes.append(
                    (
                        email.utils.format_datetime(_date),
                        f"{self.get_url_without_path()}"
                        f"/zitate/{_q.get_id_as_str()}/",
                        _q,
                    )
                )
        self.set_header("Content-Type", "application/xml")
        await self.render(
            "rss/quote_of_the_day.xml",
            quotes=quotes,
        )

    def get_redis_used_key(self, _wq_id: str) -> str:
        """Get the Redis used key."""
        return f"{self.redis_prefix}:quote-of-the-day:used:{_wq_id}"

    def get_redis_quote_date_key(self, _date: datetime | date) -> str:
        """Get the Redis key for getting quotes by date."""
        date_str = str(_date.date() if isinstance(_date, datetime) else _date)
        return f"{self.redis_prefix}:quote-of-the-day:by-date:{date_str}"

    async def has_been_used(self, _wq_id: str):
        """Check with Redis here."""
        return await self.redis.get(  # type: ignore
            self.get_redis_used_key(_wq_id)
        )

    async def set_used(self, _wq_id: str):
        """Set Redis key with used state and TTL here."""
        return await self.redis.setex(  # type: ignore
            self.get_redis_used_key(_wq_id),
            #  we have over 720 funny wrong quotes, so 420 should be ok
            420 * 24 * 60 * 60,  # TTL
            1,  # True
        )

    async def get_quote_by_date(
        self, _date: datetime | date
    ) -> None | WrongQuote:
        """Get the quote of the date if one was saved."""
        _wq_id = await self.redis.get(  # type: ignore
            self.get_redis_quote_date_key(_date)
        )
        if not _wq_id:
            return None
        _q, _a = tuple(int(_i) for _i in _wq_id.decode("utf-8").split("-"))
        return WRONG_QUOTES_CACHE.get((_q, _a))

    async def get_quote_of_today(self) -> Optional[WrongQuote]:
        """Get the quote for today."""
        _today = datetime.now(tz=timezone.utc).date()
        _wq = await self.get_quote_by_date(_today)
        if _wq:  # if was saved already
            return _wq
        quotes: tuple[WrongQuote, ...] = get_wrong_quotes(
            lambda _wq: _wq.rating > 1
        )
        count = len(quotes)
        index = random.randrange(0, count)
        for _i in range(1, count):
            quote = quotes[index]
            if await self.has_been_used(quote.get_id_as_str()):
                index = (index + 1) % count
            else:
                _wq_id = quote.get_id_as_str()
                await self.set_used(_wq_id)
                await self.redis.setex(  # type: ignore
                    self.get_redis_quote_date_key(_today),
                    30 * 24 * 60 * 60,
                    _wq_id,
                )
                return quote
        return None
