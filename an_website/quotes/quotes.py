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
from asyncio import AbstractEventLoop, Future
from typing import Any, ClassVar, Final, Literal, TypeAlias, cast

import regex
from tornado.web import HTTPError

from .. import EVENT_REDIS
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import hash_ip
from .image import QuoteAsImage, create_image
from .quote_of_the_day import QuoteOfTheDayBaseHandler
from .utils import (
    WRONG_QUOTES_CACHE,
    QuoteReadyCheckHandler,
    WrongQuote,
    create_wq_and_vote,
    get_authors,
    get_random_id,
    get_wrong_quote,
    get_wrong_quotes,
)

LOGGER: Final = logging.getLogger(__name__)


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


RatingFilter: TypeAlias = Literal["w", "n", "unrated", "rated", "all", "smart"]
SMART_RATING_FILTERS: Final[tuple[RatingFilter, ...]] = (
    *(("n",) * 1),
    *(("all",) * 5),
    *(("w",) * 5),
)


def parse_rating_filter(rating_filter_str: str) -> RatingFilter:
    """Get a rating filter."""
    match rating_filter_str:
        case "w":
            return "w"
        case "n":
            return "n"
        case "unrated":
            return "unrated"
        case "rated":
            return "rated"
        case "all":
            return "all"
    return "smart"


def get_next_id(rating_filter: RatingFilter) -> tuple[int, int]:
    """Get the id of the next quote."""
    if rating_filter == "smart":
        rating_filter = random.choice(SMART_RATING_FILTERS)  # nosec: B311

    match rating_filter:
        case "unrated":
            # get a random quote, but filter out already rated quotes
            # pylint: disable=while-used
            while (ids := get_random_id()) in WRONG_QUOTES_CACHE:
                if WRONG_QUOTES_CACHE[ids].id == -1:
                    # check for wrong quotes that are unrated but in the cache
                    # they don't have a real wrong_quotes_id
                    return ids
            return ids
        case "all":
            return get_random_id()
        case "w":
            wrong_quotes = get_wrong_quotes(lambda wq: wq.rating > 0)
        case "n":
            wrong_quotes = get_wrong_quotes(lambda wq: wq.rating < 0)
        case "rated":
            wrong_quotes = get_wrong_quotes(lambda wq: wq.id not in {-1, None})
        case _:
            wrong_quotes = ()

    if not wrong_quotes:
        # invalid rating filter or no wrong quotes with that filter
        return get_random_id()

    return random.choice(wrong_quotes).get_id()  # nosec: B311


class QuoteBaseHandler(QuoteReadyCheckHandler):
    """The base request handler for the quotes package."""

    RATELIMIT_GET_LIMIT = 20
    RATELIMIT_GET_COUNT_PER_PERIOD = 20
    RATELIMIT_GET_PERIOD = 10

    FUTURES: set[Future[Any]] = set()

    loop: AbstractEventLoop
    next_id: tuple[int, int]
    rating_filter: RatingFilter

    def future_callback(self, future: Future[WrongQuote]) -> None:
        """Discard the future and log the exception if one occured."""
        self.FUTURES.discard(future)
        if exc := future.exception():
            LOGGER.error(
                "Failed to pre-fetch quote %d-%d (%s)",
                *self.next_id,
                exc,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        else:
            LOGGER.debug("Pre-fetched quote %d-%d", *self.next_id)

    def get_next_url(self) -> str:
        """Get the URL of the next quote."""
        return self.fix_url(
            f"/zitate/{self.next_id[0]}-{self.next_id[1]}",
            r=None if self.rating_filter == "smart" else self.rating_filter,
            **{"show-rating": self.get_show_rating() or None},  # type: ignore[arg-type]
        )

    def get_show_rating(self) -> bool:
        """Return whether the user wants to see the rating."""
        return self.get_bool_argument("show-rating", False)

    def on_finish(self) -> None:
        """
        Pre-fetch the data for the next quote.

        This is done to show the users less out-of-date data.
        """
        if len(self.FUTURES) > 1 or (self.content_type or "")[:6] == "image/":
            return  # don't spam and don't do this for images

        user_agent = self.request.headers.get("User-Agent")
        if not user_agent or "bot" in user_agent.lower():
            return  # don't do this for bots

        if hasattr(self, "loop"):
            task = self.loop.create_task(
                get_wrong_quote(*self.next_id, use_cache=False)
            )
            self.FUTURES.add(task)
            task.add_done_callback(self.future_callback)

    async def prepare(self) -> None:
        """Set the id of the next wrong_quote to show."""
        await super().prepare()
        self.loop = asyncio.get_running_loop()
        self.rating_filter = parse_rating_filter(self.get_argument("r", ""))
        self.next_id = get_next_id(self.rating_filter)


class QuoteMainPage(QuoteBaseHandler, QuoteOfTheDayBaseHandler):
    """The main quote page that explains everything and links to stuff."""

    async def get(self, *, head: bool = False) -> None:
        """Render the main quote page, with a few links."""
        if head:
            return
        quote = self.get_argument("quote", "")
        author = self.get_argument("author", "")
        if (quote or author) and regex.fullmatch(r"^[0-9]+$", quote + author):
            self.redirect(self.fix_url(f"/zitate/{quote}-{author}"))
            return

        await self.render(
            "pages/quotes/main_page.html",
            funny_quote_url=self.id_to_url(
                *(
                    get_wrong_quotes(lambda wq: wq.rating > 0, shuffle=True)[
                        0
                    ].get_id()
                ),
                rating_param="w",
            ),
            random_quote_url=self.id_to_url(*self.next_id),
            quote_of_the_day=await self.get_quote_of_today(),
            one_stone_url=self.get_author_url("Albert Einstein"),
            kangaroo_url=self.get_author_url("Das Känguru"),
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
    """Redirect to the API for a random quote."""

    async def get(  # pylint: disable=unused-argument
        self, suffix: str = "", *, head: bool = False
    ) -> None:
        """Redirect to a random funny quote."""
        quote_id, author_id = get_next_id("w")
        return self.redirect(
            self.fix_url(
                f"/api/zitate/{quote_id}-{author_id}{suffix}",
            )
        )


class QuoteById(QuoteBaseHandler):
    """The page with a specified quote that then gets rendered."""

    RATELIMIT_POST_LIMIT: ClassVar[int] = 10
    RATELIMIT_POST_COUNT_PER_PERIOD: ClassVar[int] = 5
    RATELIMIT_POST_PERIOD: ClassVar[int] = 10

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        *HTMLRequestHandler.POSSIBLE_CONTENT_TYPES,
        *QuoteAsImage.POSSIBLE_CONTENT_TYPES,
    )

    LONG_PATH: ClassVar[str] = "/zitate/%d-%d"

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
            and self.rating_filter == "smart"
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
            LOGGER.warning("No Redis connection")
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

        contributed_by = f"an-website_{hash_ip(self.request.remote_ip, 10)}"

        # do the voting
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
        await self.render(
            "pages/quotes/quotes.html",
            wrong_quote=wrong_quote,
            next_href=self.get_next_url(),
            next_id=f"{self.next_id[0]}-{self.next_id[1]}",
            description=str(wrong_quote),
            rating_filter=self.rating_filter,
            rating=await self.get_rating_str(wrong_quote),
            show_rating=self.get_show_rating(),
            vote=vote,
        )

    async def update_saved_votes(
        self, quote_id: int, author_id: int, vote: int
    ) -> None:
        """Save the new vote in Redis."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)
        result = await self.redis.setex(
            self.get_redis_votes_key(quote_id, author_id),
            60 * 60 * 24 * 90,  # time to live in seconds (3 months)
            str(vote),  # value to save (the vote)
        )
        if result:
            return
        LOGGER.warning("Could not save vote in Redis: %s", result)
        raise HTTPError(500, "Could not save vote")


class QuoteAPIHandler(APIRequestHandler, QuoteById):
    """API request handler for the quotes page."""

    ALLOWED_METHODS: ClassVar[tuple[str, ...]] = ("GET", "POST")

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        *APIRequestHandler.POSSIBLE_CONTENT_TYPES,
        *QuoteAsImage.POSSIBLE_CONTENT_TYPES,
    )

    LONG_PATH: ClassVar[str] = "/api/zitate/%d-%d"

    async def render_wrong_quote(
        self, wrong_quote: WrongQuote, vote: int
    ) -> None:
        """Return the relevant data for the quotes page as JSON."""
        next_q, next_a = self.next_id
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
