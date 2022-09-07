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

import logging
from datetime import date, datetime, timedelta
from typing import ClassVar, Final

from tornado.web import HTTPError

from ...utils.request_handler import APIRequestHandler
from ..utils import (
    QuoteReadyCheckHandler,
    WrongQuote,
    get_wrong_quote,
    get_wrong_quotes,
)
from .data import QuoteOfTheDayData
from .store import (
    QUOTE_COUNT_TO_SHOW_IN_FEED,
    QuoteOfTheDayStore,
    RedisQuoteOfTheDayStore,
)

LOGGER: Final = logging.getLogger(__name__)


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
