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
from typing import Any

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo
from . import (
    WRONG_QUOTES_CACHE,
    QuoteReadyCheckHandler,
    WrongQuote,
    get_wrong_quotes,
)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitat-des-tages/feed", QuoteOfTheDayRss),
            (r"/zitat-des-tages", QuoteOfTheDayRedirect),
            (
                r"/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})",
                QuoteOfTheDayRedirect,
            ),
            (r"/api/zitat-des-tages", QuoteOfTheDayAPI),
            (
                r"/api/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})",
                QuoteOfTheDayAPI,
            ),
            (r"/api/zitat-des-tages/full", QuoteOfTheDayAPI),
            (
                r"/api/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})/full",
                QuoteOfTheDayAPI,
            ),
        ),
        name="Das Zitat des Tages",
        description="Jeden Tag ein anderes Zitat.",
        path="/zitat-des-tages",
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
    wrong_quote: WrongQuote
    url_without_path: str

    def get_quote_as_str(self, new_line_char: str = "\n") -> str:
        """Get the quote as a string with new line."""
        return (
            f"»{self.wrong_quote.quote}«{new_line_char}"
            f"- {self.wrong_quote.author}"
        )

    def get_quote_url(self) -> str:
        """Get the URL of the quote."""
        return (
            f"{self.url_without_path}/zitate/{self.wrong_quote.get_id_as_str()}"
        )

    def get_quote_image_url(self) -> str:
        """Get the URL of the image of the quote."""
        return self.get_quote_url() + ".gif"

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

    def to_json(self) -> dict[str, Any]:
        """Get the quote of the day as JSON."""
        return {
            "date": self.date.isoformat(),
            "wrong_quote": self.wrong_quote.to_json(),
            "url": self.get_quote_url(),
            "image": self.get_quote_image_url(),
        }


class QuoteOfTheDayBaseHandler(QuoteReadyCheckHandler):
    """The base request handler for the quote of the day."""

    def get_redis_used_key(self, wq_id: str) -> str:
        """Get the Redis used key."""
        return f"{self.redis_prefix}:quote-of-the-day:used:{wq_id}"

    def get_redis_quote_date_key(self, date: dt.date) -> str:
        """Get the Redis key for getting quotes by date."""
        return (
            f"{self.redis_prefix}:quote-of-the-day:by-date:{date.isoformat()}"
        )

    async def has_been_used(self, wq_id: str) -> None | bool:
        """Check with Redis here."""
        if not self.redis:
            return None
        return bool(await self.redis.get(self.get_redis_used_key(wq_id)))

    async def set_used(self, wq_id: str) -> None:
        """Set Redis key with used state and TTL here."""
        if not self.redis:
            return
        await self.redis.setex(
            self.get_redis_used_key(wq_id),
            #  we have over 720 funny wrong quotes, so 420 should be ok
            420 * 24 * 60 * 60,  # TTL
            1,  # True
        )

    def get_scheme_and_netloc(self) -> str:
        """Get the beginning of the URL."""
        return f"{self.request.protocol}://{self.request.host}"

    async def get_quote_by_date(
        self, date: dt.date
    ) -> None | QuoteOfTheDayData:
        """Get the quote of the date if one was saved."""
        if not self.redis:
            return None
        wq_id = await self.redis.get(self.get_redis_quote_date_key(date))
        if not wq_id:
            return None
        quote, author = tuple(int(x) for x in wq_id.split("-"))
        wrong_quote = WRONG_QUOTES_CACHE.get((quote, author))
        if not wrong_quote:
            return None
        return QuoteOfTheDayData(
            date, wrong_quote, self.get_scheme_and_netloc()
        )

    async def get_quote_of_today(self) -> None | QuoteOfTheDayData:
        """Get the quote for today."""
        if not self.redis:
            return None
        today = dt.datetime.now(tz=dt.timezone.utc).date()
        quote_data = await self.get_quote_by_date(today)
        if quote_data:  # if was saved already
            return quote_data
        quotes: tuple[WrongQuote, ...] = get_wrong_quotes(
            lambda wq: wq.rating > 1
        )
        count = len(quotes)
        index = random.randrange(0, count)
        for _ in range(count - 1):
            quote = quotes[index]
            if await self.has_been_used(quote.get_id_as_str()):
                index = (index + 1) % count
            else:
                wq_id = quote.get_id_as_str()
                await self.set_used(wq_id)
                await self.redis.setex(
                    self.get_redis_quote_date_key(today),
                    420 * 24 * 60 * 60,  # TTL
                    wq_id,
                )
                return QuoteOfTheDayData(
                    today, quote, self.get_scheme_and_netloc()
                )
        return None


class QuoteOfTheDayRss(QuoteOfTheDayBaseHandler):
    """The request handler for the quote of the day RSS feed."""

    IS_NOT_HTML = True

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        self.set_header("Content-Type", "application/rss+xml")
        if head:
            return
        today = dt.datetime.now(tz=dt.timezone.utc).date()
        await self.render(
            "rss/quote_of_the_day.xml",
            quotes=tuple(
                quote
                for quote in (
                    [await self.get_quote_of_today()]
                    + [
                        (
                            await self.get_quote_by_date(
                                today - dt.timedelta(days=i)
                            )
                        )
                        for i in range(1, 5)
                    ]
                )
                if quote
            ),
        )


class QuoteOfTheDayAPI(QuoteOfTheDayBaseHandler, APIRequestHandler):
    """Handler for the JSON API that returns the quote of the day."""

    async def get(self, date_str: None | str = None) -> None:
        """Handle GET requests."""
        if date_str:
            year, month, day = tuple(int(x) for x in date_str.split("-"))
            quote_data = await self.get_quote_by_date(
                dt.date(year=year, month=month, day=day)
            )
        else:
            quote_data = await self.get_quote_of_today()

        if quote_data:
            if self.request.path.endswith("/full/"):
                return await self.finish(quote_data.to_json())
            wrong_quote = quote_data.wrong_quote
            return await self.finish(
                {
                    "date": quote_data.date.isoformat(),
                    "url": quote_data.get_quote_url(),
                    "id": wrong_quote.get_id_as_str(),
                    "quote": str(wrong_quote.quote),
                    "author": str(wrong_quote.author),
                    "rating": wrong_quote.rating,
                }
            )
        raise HTTPError(404)


class QuoteOfTheDayRedirect(QuoteOfTheDayBaseHandler):
    """Redirect to the quote of the day."""

    async def get(self, date_str: None | str = None) -> None:
        """Handle GET requests."""
        if date_str:
            year, month, day = tuple(int(x) for x in date_str.split("-"))
            wrong_quote = await self.get_quote_by_date(
                dt.date(year=year, month=month, day=day)
            )
        else:
            wrong_quote = await self.get_quote_of_today()

        if wrong_quote:
            return self.redirect(
                self.fix_url(
                    wrong_quote.get_quote_url(), as_json=self.get_as_json()
                ),
                False,
            )
        raise HTTPError(404)
