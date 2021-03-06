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
A page with wrong quotes.

It displays funny, but wrong, quotes.
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from asyncio import Task
from collections.abc import Coroutine, Generator
from typing import Any, Literal, cast

from tornado.web import HTTPError, RedirectHandler

from .. import EVENT_REDIS
from ..main import IGNORED_MODULES
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, hash_ip
from . import (
    WRONG_QUOTES_CACHE,
    QuoteReadyCheckHandler,
    WrongQuote,
    create_wq_and_vote,
    get_authors,
    get_random_id,
    get_wrong_quote,
    get_wrong_quotes,
)
from .create import get_module_info as get_create_mi
from .quote_generator import get_module_info as get_generator_mi
from .quote_of_the_day import QuoteOfTheDayBaseHandler
from .quote_of_the_day import get_module_info as get_qod_mi
from .quotes_image import QuoteAsImage, create_image
from .share_page import ShareQuote

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate", QuoteMainPage),
            # {1,10} is too much, but better too much than not enough
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})", QuoteById),
            (r"/zitate/([0-9]{1,10})", QuoteById),
            (
                r"/zitate/-([0-9]{1,10})",
                RedirectHandler,
                {"url": "/zitate/info/a/{0}"},
            ),
            (
                r"/zitate/([0-9]{1,10})-",
                RedirectHandler,
                {"url": "/zitate/info/z/{0}"},
            ),
            (  # /zitate/69-420.html shouldn't say "unsupported file extension"
                r"/zitate/([0-9]{1,10})-([0-9]{1,10}).html?",
                RedirectHandler,
                {"url": "/zitate/{0}-{1}"},
            ),
            (  # redirect to the new URL
                r"/zitate/([0-9]{1,10})-([0-9]{1,10})/image\.([a-zA-Z]{3,4})",
                RedirectHandler,
                {"url": "/zitate/{0}-{1}.{2}"},
            ),
            (
                r"/zitate/([0-9]{1,10})-([0-9]{1,10})\.([a-zA-Z]{3,4})",
                QuoteAsImage,
            ),
            (
                r"/zitate/([0-9]{1,10})()\.([a-zA-Z]{3,4})",
                QuoteAsImage,
            ),
            (  # redirect to the new URL (changed because of robots.txt)
                r"/zitate/([0-9]{1,10})-([0-9]{1,10})/share",
                RedirectHandler,
                {"url": "/zitate/share/{0}-{1}"},
            ),
            (r"/zitate/share/([0-9]{1,10})-([0-9]{1,10})", ShareQuote),
            (r"/api/zitate(/full|)", QuoteRedirectAPI),
            (
                r"/api/zitate/([0-9]{1,10})-([0-9]{1,10})(?:/full|)",
                QuoteAPIHandler,
            ),
            (
                r"/api/zitate/([0-9]{1,10})(?:/full|)",
                QuoteAPIHandler,
            ),
        ),
        name="Falsch zugeordnete Zitate",
        short_name="Falsche Zitate",
        description="Witzige, aber falsch zugeordnete Zitate",
        path="/zitate",
        aliases=("/z",),
        sub_pages=(
            get_create_mi(hidden=False),
            get_generator_mi(hidden=False),
            get_qod_mi(hidden="quotes.quote_of_the_day" in IGNORED_MODULES),
        ),
        keywords=(
            "falsch",
            "zugeordnet",
            "Zitate",
            "Witzig",
            "K??nguru",
            "Marc-Uwe Kling",
            "falsche Zitate",
            "falsch zugeordnete Zitate",
        ),
    )


def vote_to_int(vote: str) -> Literal[-1, 0, 1]:
    """Parse a vote str to the corresponding int."""
    if vote == "-1":
        return -1
    if vote in {"0", "", None}:
        return 0
    if vote == "1":
        return 1

    int_vote = int(vote)
    if int_vote < 0:
        return -1
    if int_vote > 0:
        return 1

    return 0


SMART_RATING_FILTERS = (
    *(("n",) * 1),
    *(("all",) * 5),
    *(("w",) * 5),
)


class QuoteBaseHandler(QuoteReadyCheckHandler):
    """The base request handler for the quotes package."""

    RATELIMIT_GET_LIMIT = 20
    RATELIMIT_GET_COUNT_PER_PERIOD = 20
    RATELIMIT_GET_PERIOD = 10

    TASK_REFERENCES: set[Task[Any]] = set()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the base request handler."""
        super().__init__(*args, **kwargs)
        self.awaitables: list[
            Generator[Any, None, Any] | Coroutine[Any, Any, Any]
        ] = []

    def get_next_id(self, rating_filter: None | str = None) -> tuple[int, int]:
        """Get the id of the next quote."""
        if rating_filter is None:
            rating_filter = self.rating_filter()

        if rating_filter == "smart":
            rating_filter = random.choice(SMART_RATING_FILTERS)

        match rating_filter:
            case "unrated":
                # get a random quote, but filter out already rated quotes
                # pylint: disable=while-used
                while (ids := get_random_id()) in WRONG_QUOTES_CACHE:
                    if WRONG_QUOTES_CACHE[ids].id == -1:
                        # Check for wrong quotes that are unrated but in
                        # the cache. They don't have a real wrong_quotes_id.
                        return ids
                return ids
            case "all":
                return get_random_id()
            case "w":
                wrong_quotes = get_wrong_quotes(lambda wq: wq.rating > 0)
            case "n":
                wrong_quotes = get_wrong_quotes(lambda wq: wq.rating < 0)
            case "rated":
                wrong_quotes = get_wrong_quotes()
            case _:
                wrong_quotes = tuple()

        if not wrong_quotes:
            # invalid rating filter or no wrong quotes with that filter
            return get_random_id()

        return random.choice(wrong_quotes).get_id()

    def get_next_url(self) -> str:
        """Get the URL of the next quote."""
        next_q, next_a = self.get_next_id()

        return self.fix_url(
            f"/zitate/{next_q}-{next_a}",
            r=None
            if (rating_filter := self.rating_filter()) == "smart"
            else rating_filter,
            **{"show-rating": self.get_show_rating() or None},  # type: ignore[arg-type]
        )

    def get_show_rating(self) -> bool:
        """Return whether the user wants to see the rating."""
        return self.get_bool_argument("show-rating", False)

    def on_finish(self) -> None:
        """
        Request the data for the next quote, to improve performance.

        This is done to ensure that the data is always up to date.
        """
        if not self.awaitables:
            quote_id, author_id = self.get_next_id()
            task = asyncio.create_task(
                get_wrong_quote(quote_id, author_id, use_cache=False)
            )
            self.TASK_REFERENCES.add(task)
            task.add_done_callback(self.TASK_REFERENCES.discard)
        for awaitable in self.awaitables:
            task = asyncio.create_task(awaitable)
            self.TASK_REFERENCES.add(task)
            task.add_done_callback(self.TASK_REFERENCES.discard)

    def rating_filter(
        self,
    ) -> Literal["w", "n", "unrated", "rated", "all", "smart"]:
        """Get a rating filter."""
        rating_filter = self.get_argument("r", "smart")
        if rating_filter == "w":
            return "w"
        if rating_filter == "n":
            return "n"
        if rating_filter == "unrated":
            return "unrated"
        if rating_filter == "rated":
            return "rated"
        if rating_filter == "all":
            return "all"
        return "smart"


class QuoteMainPage(QuoteBaseHandler, QuoteOfTheDayBaseHandler):
    """The main quote page that explains everything and links to stuff."""

    async def get(self, *, head: bool = False) -> None:
        """Render the main quote page, with a few links."""
        if head:
            return
        quote = self.get_argument("quote", "")
        author = self.get_argument("author", "")
        if (quote or author) and re.fullmatch(r"^[0-9]+$", quote + author):
            self.redirect(self.fix_url(f"/zitate/{quote}-{author}"))
            return

        await self.render(
            "pages/quotes/quotes_main_page.html",
            funny_quote_url=self.id_to_url(
                *(
                    get_wrong_quotes(lambda wq: wq.rating > 0, shuffle=True)[
                        0
                    ].get_id()
                ),
                rating_param="w",
            ),
            random_quote_url=self.id_to_url(*self.get_next_id()),
            quote_of_the_day=await self.get_quote_of_today(),
            one_stone_url=self.get_author_url("Albert Einstein"),
            kangaroo_url=self.get_author_url("Das K??nguru"),
            muk_url=self.get_author_url("Marc-Uwe Kling"),
        )

    def get_author_url(self, author_name: str) -> None | str:
        """Get the info URL of an author."""
        authors = get_authors(lambda _a: _a.name.lower() == author_name.lower())
        if not authors:
            return None
        return self.fix_url(f"/zitate/info/a/{authors[0].id}")

    def id_to_url(
        self, quote_id: int, author_id: int, rating_param: None | str = None
    ) -> str:
        """Get the URL of a quote."""
        return self.fix_url(f"/zitate/{quote_id}-{author_id}", r=rating_param)


class QuoteRedirectAPI(APIRequestHandler, QuoteBaseHandler):
    """Redirect to the api for a random quote."""

    async def get(  # pylint: disable=unused-argument
        self, suffix: str = "", *, head: bool = False
    ) -> None:
        """Redirect to a random funny quote."""
        quote_id, author_id = self.get_next_id(rating_filter="w")
        return self.redirect(
            self.fix_url(
                f"/api/zitate/{quote_id}-{author_id}{suffix}",
            )
        )


class QuoteById(QuoteBaseHandler):
    """The page with a specified quote that then gets rendered."""

    RATELIMIT_POST_LIMIT = 10
    RATELIMIT_POST_COUNT_PER_PERIOD = 5
    RATELIMIT_POST_PERIOD = 10

    POSSIBLE_CONTENT_TYPES = (
        *HTMLRequestHandler.POSSIBLE_CONTENT_TYPES,
        *QuoteAsImage.POSSIBLE_CONTENT_TYPES,
    )

    LONG_PATH = "/zitate/%d-%d"

    async def get(
        self, quote_id: str, author_id: None | str = None, *, head: bool = False
    ) -> None:
        """Handle GET requests to this page and render the quote."""
        int_quote_id = int(quote_id)
        if author_id is None:
            wqs = get_wrong_quotes(lambda wq: wq.id == int_quote_id)
            if not wqs:
                raise HTTPError(404, f"No wrong quote with id {quote_id}")
            return self.redirect(
                self.fix_url(
                    self.LONG_PATH % (wqs[0].quote.id, wqs[0].author.id)
                )
            )
        if self.content_type and self.content_type.startswith("image/"):
            _wq = await get_wrong_quote(int_quote_id, int(author_id))
            return await self.finish(
                create_image(
                    _wq.quote.quote,
                    _wq.author.name,
                    _wq.rating,
                    f"{self.request.host_name}/z/{_wq.get_id_as_str(True)}",
                    self.content_type.removeprefix("image/"),
                )
            )
        if head:
            return
        await self.render_quote(int_quote_id, int(author_id))

    async def get_old_vote(
        self, quote_id: int, author_id: int
    ) -> Literal[-1, 0, 1]:
        """Get the old vote from the saved vote."""
        old_vote = await self.get_saved_vote(quote_id, author_id)
        if old_vote is None:
            return 0
        return old_vote

    async def get_rating_str(self, wrong_quote: WrongQuote) -> str:
        """Get the rating str to display on the page."""
        if wrong_quote.id in {None, -1}:
            return "---"
        if (
            not self.get_show_rating()  # don't hide the rating on wish of user
            and self.rating_filter() == "smart"
            and self.request.method
            and self.request.method.upper() == "GET"
            and await self.get_saved_vote(
                wrong_quote.quote.id, wrong_quote.author.id
            )
            is None
        ):
            return "???"
        return str(wrong_quote.rating)

    def get_redis_votes_key(self, quote_id: int, author_id: int) -> str:
        """Get the key to save the votes with Redis."""
        return (
            f"{self.redis_prefix}:quote-votes:"
            f"{self.get_user_id()}:{quote_id}-{author_id}"
        )

    async def get_saved_vote(
        self, quote_id: int, author_id: int
    ) -> None | Literal[-1, 0, 1]:
        """
        Get the vote of the current user saved with Redis.

        Use the quote_id and author_id to query the vote.
        Return None if nothing is saved.
        """
        if not EVENT_REDIS.is_set():
            logger.warning("No Redis connection")
            return 0
        result = await self.redis.get(
            self.get_redis_votes_key(quote_id, author_id)
        )
        if result == "-1":
            return -1
        if result == "0":
            return 0
        if result == "1":
            return 1
        return None

    async def post(self, quote_id_str: str, author_id_str: str) -> None:
        """
        Handle POST requests to this page and render the quote.

        This is used to vote the quote, without changing the URL.
        """
        quote_id = int(quote_id_str)
        author_id = int(author_id_str)

        new_vote_str = self.get_argument("vote", None)

        if not new_vote_str:
            return await self.render_quote(quote_id, author_id)

        old_vote: Literal[-1, 0, 1] = await self.get_old_vote(
            quote_id, author_id
        )

        new_vote: Literal[-1, 0, 1] = vote_to_int(new_vote_str)
        vote_diff: int = new_vote - old_vote

        if not vote_diff:  # == 0
            return await self.render_quote(quote_id, author_id)

        await self.update_saved_votes(quote_id, author_id, new_vote)

        to_vote = cast(Literal[-1, 1], -1 if vote_diff < 0 else 1)

        contributed_by = f"an-website_{hash_ip(str(self.request.remote_ip))}"

        # do the voting:
        wrong_quote = await create_wq_and_vote(
            to_vote, quote_id, author_id, contributed_by
        )
        if abs(vote_diff) == 2:
            await wrong_quote.vote(to_vote, lazy=True)

        await self.render_wrong_quote(wrong_quote, new_vote)

    async def render_quote(self, quote_id: int, author_id: int) -> None:
        """Get and render a wrong quote based on author id and author id."""
        await self.render_wrong_quote(
            await get_wrong_quote(quote_id, author_id),
            await self.get_old_vote(quote_id, author_id),
        )

    async def render_wrong_quote(
        self, wrong_quote: WrongQuote, vote: int
    ) -> None:
        """Render the page with the wrong_quote and this vote."""
        next_q, next_a = self.get_next_id()
        await self.render(
            "pages/quotes/quotes.html",
            wrong_quote=wrong_quote,
            next_href=self.get_next_url(),
            next_id=f"{next_q}-{next_a}",
            description=str(wrong_quote),
            rating_filter=self.rating_filter(),
            rating=await self.get_rating_str(wrong_quote),
            show_rating=self.get_show_rating(),
            vote=vote,
        )

    async def update_saved_votes(
        self, quote_id: int, author_id: int, vote: int
    ) -> None:
        """Save the new vote in Redis."""
        result = None
        if EVENT_REDIS.is_set():
            result = await self.redis.setex(
                self.get_redis_votes_key(quote_id, author_id),
                60 * 60 * 24 * 90,  # time to live in seconds (3 months)
                str(vote),  # value to save (the vote)
            )
        if not result:
            logger.warning("Could not save vote in Redis: %s", result)
            raise HTTPError(500, "Could not save vote in Redis")


class QuoteAPIHandler(APIRequestHandler, QuoteById):
    """API request handler for the quotes page."""

    ALLOWED_METHODS = ("GET", "POST")

    POSSIBLE_CONTENT_TYPES = (
        *APIRequestHandler.POSSIBLE_CONTENT_TYPES,
        *QuoteAsImage.POSSIBLE_CONTENT_TYPES,
    )

    LONG_PATH = "/api/zitate/%d-%d"

    async def render_wrong_quote(
        self, wrong_quote: WrongQuote, vote: int
    ) -> None:
        """Return the relevant data for the quotes page as JSON."""
        next_q, next_a = self.get_next_id()
        if self.request.path.endswith("/full"):
            return await self.finish_dict(
                wrong_quote=wrong_quote.to_json(),
                next=f"{next_q}-{next_a}",
                vote=vote,
            )
        return await self.finish_dict(
            id=wrong_quote.get_id_as_str(),
            quote=str(wrong_quote.quote),
            author=str(wrong_quote.author),
            real_author=str(wrong_quote.quote.author),
            real_author_id=wrong_quote.quote.author.id,
            rating=await self.get_rating_str(wrong_quote),
            vote=vote,
            next=f"{next_q}-{next_a}",
        )
