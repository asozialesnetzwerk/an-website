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

"""
The quotes page of the website.

It displays funny, but wrong, quotes.
"""
from __future__ import annotations

import logging
import random
from functools import cache
from typing import Literal, Optional

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo
from . import (
    WRONG_QUOTES_CACHE,
    QuoteReadyCheckRequestHandler,
    WrongQuote,
    create_wq_and_vote,
    get_random_id,
    get_wrong_quote,
    get_wrong_quotes,
)
from .quotes_img import QuoteAsImg
from .share_page import ShareQuote

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate/", QuoteMainPage),
            # {1,10} is too much, but better too much than not enough
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})/", QuoteById),
            (r"/zitate/([0-9]{1,10})/", QuoteById),
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})/image.png", QuoteAsImg),
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})/share/", ShareQuote),
            (r"/api/zitate/([0-9]{1,10})-([0-9]{1,10})/", QuoteAPIHandler),
        ),
        name="Falsche Zitate",
        description="Eine Webseite mit falsch zugeordneten Zitaten",
        path="/zitate/",
        aliases=("/z/",),
        keywords=(
            "falsch",
            "zugeordnet",
            "Zitate",
            "Witzig",
            "Känguru",
        ),
    )


def vote_to_int(vote: str) -> Literal[-1, 0, 1]:
    """Parse a vote str to the corresponding int."""
    if vote == "-1":
        return -1
    if vote in ("0", str(), None):
        return 0
    if vote == "1":
        return 1

    int_vote = int(vote)
    if int_vote < 0:
        return -1
    if int_vote > 0:
        return 1

    return 0


def get_random_rating_filter() -> str:
    """Get a random rating filter with smart probabilities."""
    rand_int = random.randint(0, 27)
    if rand_int < 2:  # 0 - 1 → 2 → ~7.14%
        return "n"
    if rand_int < 9:  # 2 - 8 → 7 → 25%
        return "unrated"
    if rand_int < 15:  # 9 - 14 → 6 → ~21.43%
        return "all"
    # 15 - 27 → 13 → 46.43%
    return "w"


class QuoteBaseHandler(QuoteReadyCheckRequestHandler):
    """The base request handler for the quotes package."""

    @cache
    def rating_filter(self):
        """Get a rating filter."""
        rating_filter = self.get_query_argument("r", default="smart")
        if rating_filter not in ("w", "n", "unrated", "rated", "all"):
            return "smart"
        return rating_filter

    def get_next_url(self) -> str:
        """Get the URL of the next quote."""
        next_q, next_a = self.get_next_id()
        url = f"/zitate/{next_q}-{next_a}/"
        if (rating_filter := self.rating_filter()) != "smart":
            url = f"{url}?r={rating_filter}"

        return self.fix_url(url)

    @cache
    def get_next_id(  # noqa: C901
        self, rating_filter: str = None
    ) -> tuple[int, int]:
        """Get the id of the next quote."""
        if rating_filter is None:
            rating_filter = self.rating_filter()
        if rating_filter == "smart":
            rating_filter = get_random_rating_filter()

        if rating_filter == "unrated":
            # get a random quote, but filter out already rated quotes
            while (ids := get_random_id()) in WRONG_QUOTES_CACHE:
                if WRONG_QUOTES_CACHE[ids].id == -1:
                    # Check for wrong quotes, that are unrated but in
                    # the cache. They don't have a real wrong_quotes_id
                    return ids
            return ids
        if rating_filter == "all":
            return get_random_id()

        wrong_quotes = None
        if rating_filter == "w":
            wrong_quotes = get_wrong_quotes(lambda _wq: _wq.rating > 0)
        elif rating_filter == "n":
            wrong_quotes = get_wrong_quotes(lambda _wq: _wq.rating < 0)
        elif rating_filter == "rated":
            wrong_quotes = get_wrong_quotes()

        if not wrong_quotes:
            return get_random_id()

        return random.choice(wrong_quotes).get_id()

    def on_finish(self):
        """
        Request the data for the next quote, to improve performance.

        This is done to ensure that the data is always up to date.
        """
        # quote_id, author_id = self.get_next_id()
        # asyncio.run_coroutine_threadsafe(
        #     get_wrong_quote(quote_id, author_id, use_cache=False),
        #     asyncio.get_event_loop(),
        # )


class QuoteMainPage(QuoteBaseHandler):
    """The main quote page that should render a random quote."""

    async def get(self):
        """Handle the GET request to the main quote page and render a quote."""
        quote_id, author_id = self.get_next_id(rating_filter="w")
        self.redirect(self.fix_url(f"/zitate/{quote_id}-{author_id}"))


class QuoteById(QuoteBaseHandler):
    """The page with a specified quote that then gets rendered."""

    async def get(self, quote_id: str, author_id: str = None):
        """Handle the GET request to this page and render the quote."""
        int_quote_id = int(quote_id)
        if author_id is None:
            _wqs = get_wrong_quotes(lambda _wq: _wq.id == int_quote_id)
            if not _wqs:
                raise HTTPError(404, f"No wrong quote with id {quote_id}")
            return self.redirect(
                self.fix_url(
                    f"/zitate/{_wqs[0].quote.id}-{_wqs[0].author.id}/"
                )
            )
        await self.render_quote(int_quote_id, int(author_id))

    async def post(self, quote_id_str: str, author_id_str: str):
        """
        Handle the POST request to this page and render the quote.

        This is used to vote the quote, without changing the URL.
        """
        quote_id = int(quote_id_str)
        author_id = int(author_id_str)
        new_vote_str = self.get_argument("vote", default=None)
        if new_vote_str is None or new_vote_str == str():
            return await self.render_quote(quote_id, author_id)

        old_vote = await self.get_old_vote(quote_id, author_id)

        if (vote := vote_to_int(new_vote_str)) == old_vote:
            return await self.render_quote(quote_id, author_id)

        await self.update_saved_votes(quote_id, author_id, vote)

        contributed_by = self.get_argument("user-name", default=str())
        if contributed_by is not None:
            contributed_by = contributed_by.strip()
        if contributed_by is None or len(contributed_by) < 2:
            contributed_by = f"an-website_{self.get_hashed_remote_ip()}"
        # do the voting:
        if vote > old_vote:
            wrong_quote = await create_wq_and_vote(
                1, quote_id, author_id, contributed_by
            )
            if vote - old_vote == 2:  # TODO: add better fix
                wrong_quote = await create_wq_and_vote(
                    1, quote_id, author_id, contributed_by, True
                )
        elif vote < old_vote:
            wrong_quote = await create_wq_and_vote(
                -1, quote_id, author_id, contributed_by
            )
            if vote - old_vote == -2:  # TODO: add better fix
                wrong_quote = await create_wq_and_vote(
                    -1, quote_id, author_id, contributed_by, True
                )
        else:
            raise HTTPError(500)
        await self.render_wrong_quote(wrong_quote, vote)

    async def render_wrong_quote(self, wrong_quote: WrongQuote, vote: int):
        """Render the page with the wrong_quote and this vote."""
        next_q, next_a = self.get_next_id()
        return await self.render(
            "pages/quotes/quotes.html",
            wrong_quote=wrong_quote,
            next_href=self.get_next_url(),
            next_id=f"{next_q}-{next_a}",
            description=str(wrong_quote),
            rating_filter=self.rating_filter(),
            rating=await self.get_rating_str(wrong_quote),
            vote=vote,
        )

    async def get_rating_str(self, wrong_quote: WrongQuote) -> str:
        """Get the rating str to display on the page."""
        if wrong_quote.id in (None, -1):
            return "---"
        if (
            self.rating_filter() == "smart"
            and await self.get_saved_vote(
                wrong_quote.quote.id, wrong_quote.author.id
            )
            is None
        ):
            return "???"
        return str(wrong_quote.rating)

    async def render_quote(self, quote_id: int, author_id: int):
        """Get and render a wrong quote based on author id and author id."""
        return await self.render_wrong_quote(
            await get_wrong_quote(quote_id, author_id),
            await self.get_old_vote(quote_id, author_id),
        )

    @cache
    def get_redis_votes_key(self, quote_id: int, author_id: int) -> str:
        """Get the key to save the votes with Redis."""
        prefix = self.settings.get("REDIS_PREFIX")
        user_id = self.get_user_id()
        return f"{prefix}:quote-votes:{user_id}:{quote_id}-{author_id}"

    async def update_saved_votes(
        self, quote_id: int, author_id: int, vote: int
    ):
        """Save the new vote in the cookies."""
        redis = self.settings["REDIS"]
        result = await redis.setex(
            self.get_redis_votes_key(quote_id, author_id),
            60 * 60 * 24 * 90,  # time to live in seconds (3 months)
            str(vote),  # value to save (the vote)
        )
        if result not in (True, "OK"):
            logger.warning("Could not save vote in Redis: %s", result)
            raise HTTPError(500, "Could not save vote in Redis")

    async def get_old_vote(
        self, quote_id: int, author_id: int
    ) -> Literal[-1, 0, 1]:
        """Get the old vote from the saved vote."""
        old_vote = await self.get_saved_vote(quote_id, author_id)
        if old_vote is None:
            return 0
        return old_vote

    async def get_saved_vote(
        self, quote_id: int, author_id: int
    ) -> Optional[Literal[-1, 0, 1]]:
        """
        Get the vote of the current user saved with Redis.

        Use the quote_id and author_id to query the vote.
        Return None if nothing is saved.
        """
        if "REDIS" not in self.settings:
            logger.warning("No Redis connection")
            return 0
        result = await self.settings["REDIS"].get(
            self.get_redis_votes_key(quote_id, author_id)
        )
        if result in ("-1", b"-1"):
            return -1
        if result in ("0", b"0"):
            return 0
        if result in ("1", b"1"):
            return 1
        return None


class QuoteAPIHandler(QuoteById, APIRequestHandler):
    """API request handler for the quotes page."""

    RATELIMIT_TOKENS = 1
    RATELIMIT_NAME = "quotes-api"
    ALLOWED_METHODS = ("GET", "POST")

    async def render_wrong_quote(self, wrong_quote: WrongQuote, vote: int):
        """Return the relevant data for the quotes page as JSON."""
        next_q, next_a = self.get_next_id()
        return await self.finish(
            {
                "id": wrong_quote.get_id_as_str(),
                "quote": wrong_quote.quote.quote,
                "author": wrong_quote.author.name,
                "rating": await self.get_rating_str(wrong_quote),
                "vote": vote,
                "next": f"{next_q}-{next_a}",
            }
        )
