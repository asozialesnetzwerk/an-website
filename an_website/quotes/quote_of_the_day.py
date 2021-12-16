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

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler
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
        handlers=(
            (r"/zitat-des-tages/feed/", QuoteOfTheDayRss),
            (r"/zitat-des-tages/", QuoteOfTheDayRedirect),
            (
                r"/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})/",
                QuoteOfTheDayRedirect,
            ),
            (r"/api/zitat-des-tages/", QuoteOfTheDayAPI),
            (
                r"/api/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})/",
                QuoteOfTheDayAPI,
            ),
        ),
        name="Das Zitat des Tages",
        description="Jeden Tag ein anderes Zitat.",
        path="/zitat-des-tages/",
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

    date: dt.date
    quote: WrongQuote
    url_without_path: str

    def get_quote_as_str(self, new_line_char="\n") -> str:
        """Get the quote as a string with new line."""
        return f"»{self.quote.quote}«{new_line_char}- {self.quote.author}"

    def get_quote_url(self) -> str:
        """Get the URL of the quote."""
        return f"{self.url_without_path}/zitate/{self.quote.get_id_as_str()}/"

    def get_quote_image_url(self) -> str:
        """Get the URL of the image of the quote."""
        return self.get_quote_url() + "image.png"

    def get_date_for_rss(self) -> str:
        """Get the date as specified in RFC 2822."""
        return email.utils.format_datetime(
            dt.datetime(
                year=self.date.year,
                month=self.date.month,
                day=self.date.day,
                tzinfo=dt.timezone.utc,
            ),
            True,
        )

    def get_title(self) -> str:
        """Get the title for the quote of the day."""
        return f"Das Zitat des Tages vom {self.date:%d. %m. %Y}"

    def to_json(self) -> dict:
        """Get the quote of the day as json."""
        return {
            "date": self.date.isoformat(),
            "quote": self.quote.to_json(),
            "url": self.get_quote_url(),
            "image": self.get_quote_image_url(),
        }


class QuoteOfTheDayBaseHandler(QuoteReadyCheckRequestHandler):
    """The base request handler for the quote of the day."""

    def get_redis_used_key(self, _wq_id: str) -> str:
        """Get the Redis used key."""
        return f"{self.redis_prefix}:quote-of-the-day:used:{_wq_id}"

    def get_redis_quote_date_key(self, date: dt.date) -> str:
        """Get the Redis key for getting quotes by date."""
        return (
            f"{self.redis_prefix}:quote-of-the-day:by-date:{date.isoformat()}"
        )

    async def has_been_used(self, _wq_id: str):
        """Check with Redis here."""
        return await self.redis.get(self.get_redis_used_key(_wq_id))

    async def set_used(self, _wq_id: str):
        """Set Redis key with used state and TTL here."""
        return await self.redis.setex(
            self.get_redis_used_key(_wq_id),
            #  we have over 720 funny wrong quotes, so 420 should be ok
            420 * 24 * 60 * 60,  # TTL
            1,  # True
        )

    async def get_quote_by_date(
        self, date: dt.date
    ) -> None | QuoteOfTheDayData:
        """Get the quote of the date if one was saved."""
        _wq_id = await self.redis.get(self.get_redis_quote_date_key(date))
        if not _wq_id:
            return None
        _q, _a = tuple(int(_i) for _i in _wq_id.decode("utf-8").split("-"))
        _wq = WRONG_QUOTES_CACHE.get((_q, _a))
        if not _wq:
            return None
        return QuoteOfTheDayData(date, _wq, self.get_url_without_path())

    async def get_quote_of_today(self) -> None | QuoteOfTheDayData:
        """Get the quote for today."""
        if not self.redis:
            return None
        today = dt.datetime.now(tz=dt.timezone.utc).date()
        quote_data = await self.get_quote_by_date(today)
        if quote_data:  # if was saved already
            return quote_data
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
                await self.redis.setex(
                    self.get_redis_quote_date_key(today),
                    420 * 24 * 60 * 60,  # TTL
                    _wq_id,
                )
                return QuoteOfTheDayData(
                    today, quote, self.get_url_without_path()
                )
        return None


class QuoteOfTheDayRss(QuoteOfTheDayBaseHandler):
    """The request handler for the quote of the day RSS feed."""

    async def get(self):
        """Handle GET requests."""
        today = dt.datetime.now(tz=dt.timezone.utc).date()
        self.set_header("Content-Type", "application/rss+xml")
        await self.render(
            "rss/quote_of_the_day.xml",
            quotes=tuple(
                _q
                for _q in (
                    [await self.get_quote_of_today()]
                    + [
                        (
                            await self.get_quote_by_date(
                                today - dt.timedelta(days=_i)
                            )
                        )
                        for _i in range(1, 5)
                    ]
                )
                if _q
            ),
        )


class QuoteOfTheDayAPI(QuoteOfTheDayBaseHandler, APIRequestHandler):
    """Handler for the JSON API that returns the quote of the day."""

    async def get(self, _date_str: str = None):
        """Handle get requests."""
        if _date_str:
            _y, _m, _d = tuple(int(_i) for _i in _date_str.split("-"))
            _wq = await self.get_quote_by_date(
                dt.date(year=_y, month=_m, day=_d)
            )
        else:
            _wq = await self.get_quote_of_today()

        if _wq:
            await self.finish(_wq.to_json())
        raise HTTPError(404)


class QuoteOfTheDayRedirect(QuoteOfTheDayBaseHandler):
    """Redirect to the quote of the day."""

    async def get(self, _date_str: str = None):
        """Handle GET requests."""
        if _date_str:
            _y, _m, _d = tuple(int(_i) for _i in _date_str.split("-"))
            _wq = await self.get_quote_by_date(
                dt.date(year=_y, month=_m, day=_d)
            )
        else:
            _wq = await self.get_quote_of_today()

        if _wq:
            self.redirect(
                _wq.get_quote_url(),
                False,
            )
        raise HTTPError(404)
