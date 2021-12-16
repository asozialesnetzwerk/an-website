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

import dataclasses
import datetime as dt
import email.utils
import random

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


@dataclasses.dataclass
class QuoteOfTheDayData:
    """The class representing data for the quote of the day."""

    date: dt.datetime
    quote: WrongQuote
    url_without_path: str

    def get_quote_as_str(self) -> str:
        """Get the quote as a string with new line."""
        return f"»{self.quote.quote}«\n- {self.quote.author}"

    def get_quote_url(self) -> str:
        """Get the URL of the quote."""
        return f"{self.url_without_path}/zitate/{self.quote.get_id_as_str()}/"

    def get_quote_image_url(self) -> str:
        """Get the URL of the image of the quote."""
        return self.get_quote_url() + "image.png"

    def get_date_for_rss(self) -> str:
        """Get the date as specified in RFC 2822."""
        return email.utils.format_datetime(self.date)

    def get_title(self) -> str:
        """Get the title for the quote of the day."""
        return f"Das Zitat des Tages vom {self.date:%d. %m. %Y}"


class QuoteOfTheDayRss(QuoteReadyCheckRequestHandler):
    """The base request handler for the quotes package."""

    async def get(self):
        """Handle GET requests."""
        _today_date = dt.datetime.now(tz=dt.timezone.utc).date()
        today = dt.datetime(
            year=_today_date.year,
            month=_today_date.month,
            day=_today_date.day,
            tzinfo=dt.timezone.utc,
        )
        quote = await self.get_quote_of_today()
        quotes: list[QuoteOfTheDayData] = [
            QuoteOfTheDayData(today, quote, self.get_url_without_path())
        ]
        for _i in range(1, 5):
            date = today - dt.timedelta(days=_i)
            _wq = await self.get_quote_by_date(date)
            if _wq:
                quotes.append(
                    QuoteOfTheDayData(
                        date,
                        _wq,
                        self.get_url_without_path(),
                    )
                )
        self.set_header("Content-Type", "application/rss+xml")
        await self.render(
            "rss/quote_of_the_day.xml",
            quotes=quotes,
        )

    def get_redis_used_key(self, _wq_id: str) -> str:
        """Get the Redis used key."""
        return f"{self.redis_prefix}:quote-of-the-day:used:{_wq_id}"

    def get_redis_quote_date_key(self, date: dt.date) -> str:
        """Get the Redis key for getting quotes by date."""
        date_str = str(date.date() if isinstance(date, dt.datetime) else date)
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

    async def get_quote_by_date(self, _date: dt.date) -> None | WrongQuote:
        """Get the quote of the date if one was saved."""
        _wq_id = await self.redis.get(  # type: ignore
            self.get_redis_quote_date_key(_date)
        )
        if not _wq_id:
            return None
        _q, _a = tuple(int(_i) for _i in _wq_id.decode("utf-8").split("-"))
        return WRONG_QUOTES_CACHE.get((_q, _a))

    async def get_quote_of_today(self) -> WrongQuote | None:
        """Get the quote for today."""
        _today = dt.datetime.now(tz=dt.timezone.utc).date()
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
