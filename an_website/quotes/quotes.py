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

import asyncio
import logging
import random
from dataclasses import dataclass
from functools import cache
from typing import Literal

import orjson as json
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo

API_URL: str = "https://zitate.prapsschnalinen.de/api"

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate/", QuoteMainPage),
            # {1,10} is too much, but better too much than not enough
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})/", QuoteById),
        ),
        name="Falsch zugeordnete Zitate",
        description="Eine Website mit falsch zugeordneten Zitaten",
        path="/zitate/",
        keywords=(
            "falsch",
            "zugeordnet",
            "Zitate",
            "Witzig",
            "Känguru",
        ),
    )


@dataclass
class QuotesObjBase:
    """An object with an id."""

    id: int  # pylint: disable=invalid-name

    def get_id_as_str(self):
        """Get the id of the object as a string."""
        return str(self.id)

    def __str__(self):
        """Return a basic string with the id."""
        return f"QuotesObj({self.id})"


@dataclass
class Author(QuotesObjBase):
    """The author object with a name."""

    name: str

    def update_name(self, name: str):
        """Update author data with another author."""
        if self.name != name:
            self.name = name

    def __str__(self):
        """Return the name of the author."""
        return self.name.strip()


@dataclass
class Quote(QuotesObjBase):
    """The quote object with a quote text and an author."""

    quote: str
    author: Author

    def update_quote(self, quote: str, author_id: int, author_name: str):
        """Update quote data with new data."""
        self.quote = quote
        if self.author.id == author_id:
            self.author.update_name(author_name)
            return
        author = AUTHORS_CACHE.setdefault(
            author_id,
            Author(author_id, author_name),
        )
        author.update_name(author_name)
        self.author = author

    def __str__(self):
        """Return the the content of the quote."""
        return self.quote.strip()


@dataclass
class WrongQuote(QuotesObjBase):
    """The wrong quote object with a quote, an author and a rating."""

    quote: Quote
    author: Author
    rating: int

    def get_id(self) -> tuple[int, int]:
        """
        Get the id of the quote and the author in a tuple.

        :return tuple(quote_id, author_id)
        """
        return self.quote.id, self.author.id

    def get_id_as_str(self):
        """
        Get the id of the wrong quote as a string.

        Format: quote_id-author_id
        """
        return f"{self.quote.id}-{self.author.id}"

    def __str__(self):
        r"""
        Return the wrong quote.

        like: '»quote«\n - author'.
        """
        return f"»{self.quote}« - {self.author}"


QUOTES_CACHE: dict[int, Quote] = {}
AUTHORS_CACHE: dict[int, Author] = {}
WRONG_QUOTES_CACHE: dict[tuple[int, int], WrongQuote] = {}


async def make_api_request(end_point: str, args: str = "") -> dict:
    """Make api request and return the result as dict."""
    http_client = AsyncHTTPClient()
    response = await http_client.fetch(
        f"{API_URL}/{end_point}?{args}", raise_error=True
    )
    return json.loads(response.body)


async def start_updating_cache_periodically():
    """Start updating the cache every hour."""
    while True:
        logger.info("Update quotes cache.")
        await update_cache()
        await asyncio.sleep(60 * 60)


async def update_cache():
    """Fill the cache with all data from the api."""
    json_data = await make_api_request("wrongquotes")
    for wrong_quote in json_data:
        parse_wrong_quote(wrong_quote)

    json_data = await make_api_request("quotes")
    for quote in json_data:
        parse_quote(quote)

    json_data = await make_api_request("authors")
    for author in json_data:
        parse_author(author)


async def get_author_by_id(author_id: int) -> Author:
    """Get an author by its id."""
    author = AUTHORS_CACHE.get(author_id, None)
    if author is not None:
        return author

    return parse_author(await make_api_request(f"authors/{author_id}"))


def parse_author(json_data: dict) -> Author:
    """Parse a author from json data."""
    author_id = json_data["id"]
    name = json_data["author"]
    author = AUTHORS_CACHE.setdefault(
        author_id, Author(author_id, json_data["author"])
    )
    author.update_name(name)
    return author


async def get_quote_by_id(quote_id: int) -> Quote:
    """Get a quote by its id."""
    quote = QUOTES_CACHE.get(quote_id, None)
    if quote is not None:
        return quote
    return parse_quote(await make_api_request(f"quotes/{quote_id}"))


def parse_quote(json_data: dict) -> Quote:
    """Parse a quote from json data."""
    quote_id = json_data["id"]
    author = parse_author(json_data["author"])
    quote = QUOTES_CACHE.setdefault(
        quote_id,
        Quote(
            quote_id,
            json_data["quote"],
            author,
        ),
    )
    quote.update_quote(
        json_data["quote"],
        author.id,
        author.name,
    )
    return quote


async def get_wrong_quote(
    quote_id: int, author_id: int, use_cache=True
) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    wrong_quote_id = (quote_id, author_id)
    wrong_quote = WRONG_QUOTES_CACHE.get(wrong_quote_id, None)
    if use_cache and wrong_quote is not None:
        return wrong_quote

    if not use_cache and wrong_quote is not None and wrong_quote.id != -1:
        # use the id of the wrong quote to get the data more efficient
        return parse_wrong_quote(
            await make_api_request(f"wrongquotes/{wrong_quote.id}")
        )
    if use_cache and quote_id in QUOTES_CACHE and author_id in AUTHORS_CACHE:
        # we don't need to request anything, as the wrong_quote probably has
        # no ratings just use the cached quote and author
        return WrongQuote(
            -1,
            QUOTES_CACHE[quote_id],
            AUTHORS_CACHE[author_id],
            0,
        )
    result = await make_api_request(
        "wrongquotes",
        f"quote={quote_id}&author={author_id}&simulate=true",
    )
    if len(result) > 0:
        return parse_wrong_quote(result[0])

    return WrongQuote(
        -1,
        await get_quote_by_id(quote_id),
        await get_author_by_id(author_id),
        rating=0,
    )


def parse_wrong_quote(json_data: dict) -> WrongQuote:
    """Parse a quote."""
    id_tuple = (json_data["quote"]["id"], json_data["author"]["id"])
    rating = json_data["rating"]
    wrong_quote_id = json_data.get("id", -1)
    if wrong_quote_id is None:
        wrong_quote_id = -1
    wrong_quote = WRONG_QUOTES_CACHE.setdefault(
        id_tuple,
        WrongQuote(
            id=wrong_quote_id,
            quote=parse_quote(json_data["quote"]),
            author=parse_author(json_data["author"]),
            rating=rating,
        ),
    )
    assert (wrong_quote.quote.id, wrong_quote.author.id) == id_tuple
    if wrong_quote.rating != rating:
        wrong_quote.rating = rating
    if wrong_quote.id != wrong_quote_id:
        wrong_quote.id = wrong_quote_id
    return wrong_quote


async def get_rating_by_id(quote_id: int, author_id: int) -> int:
    """Get the rating of a wrong quote."""
    return (await get_wrong_quote(quote_id, author_id)).rating


def get_random_quote_id() -> int:
    """Get random quote id."""
    return random.randint(0, max((*QUOTES_CACHE.keys(), 100)))


def get_random_author_id() -> int:
    """Get random author id."""
    return random.randint(0, max((*AUTHORS_CACHE.keys(), 100)))


def get_random_id() -> tuple[int, int]:
    """Get random wrong quote id."""
    return (
        get_random_quote_id(),
        get_random_author_id(),
    )


async def vote_wrong_quote(
    vote: Literal[-1, 1], wrong_quote: WrongQuote
) -> WrongQuote:
    """Vote for the wrong_quote with the given id."""
    http_client = AsyncHTTPClient()
    response = await http_client.fetch(
        f"{API_URL}/wrongquotes/{wrong_quote.id}",
        method="POST",
        body=f"vote={vote}",
    )
    return parse_wrong_quote(json.loads(response.body))


async def create_wq_and_vote(
    vote: Literal[-1, 1],
    quote_id: int,
    author_id: int,
    identifier: str,
) -> WrongQuote:
    """
    Vote for the wrong_quote with the api.

    If the wrong_quote doesn't exist yet, create it.
    """
    wrong_quote = WRONG_QUOTES_CACHE.get((quote_id, author_id), None)
    if wrong_quote is not None and wrong_quote.id != -1:
        return await vote_wrong_quote(vote, wrong_quote)
    # we don't know the wrong_quote_id, so we have to create the wrong_quote
    http_client = AsyncHTTPClient()
    response = await http_client.fetch(
        f"{API_URL}/wrongquotes",
        method="POST",
        body=f"quote={quote_id}&"
        f"author={author_id}&"
        f"contributed_by=an-website_{identifier}",
    )
    wrong_quote = parse_wrong_quote(json.loads(response.body))
    return await vote_wrong_quote(vote, wrong_quote)


def vote_to_int(vote: str) -> Literal[-1, 0, 1]:
    """Parse a vote str to the corresponding int."""
    if vote == "-1":
        return -1
    if vote in ("0", "", None):
        return 0
    if vote == "1":
        return 1

    int_vote = int(vote)
    if int_vote < 0:
        return -1
    if int_vote > 0:
        return 1

    return 0


class QuoteBaseHandler(BaseRequestHandler):
    """The base request handler for the quotes package."""

    @cache
    def rating_filter(self):
        """Get a rating filter."""
        rating_filter = self.get_query_argument("r", default="smart")
        if rating_filter not in ("w", "n", "unrated", "rated", "all"):
            return "smart"
        return rating_filter

    def get_next_url(self) -> str:
        """Get the url of the next quote."""
        next_q, next_a = self.get_next_id()
        url = f"/zitate/{next_q}-{next_a}/"
        if (rating_filter := self.rating_filter()) != "smart":
            return url + f"?r={rating_filter}"
        return url

    @cache
    def get_next_id(self) -> tuple[int, int]:  # noqa: C901
        """Get the id of the next quote."""
        rating_filter = self.rating_filter()
        if rating_filter == "smart":
            rand_int = random.randint(0, 27)
            if rand_int < 2:  # 0 - 1 → 2 → ~7.14%
                rating_filter = "n"
            elif rand_int < 9:  # 2 - 8 → 7 → 25%
                rating_filter = "unrated"
            elif rand_int < 15:  # 9 - 14 → 6 → ~21.43%
                rating_filter = "all"
            else:  # 15 - 27 → 13 → 46.43%
                rating_filter = "w"

        if rating_filter == "w":
            return random.choice(
                tuple(  # raises an error if called shortly after start
                    filter(
                        lambda _wq: _wq.rating > 0, WRONG_QUOTES_CACHE.values()
                    )
                )
            ).get_id()
        if rating_filter == "n":
            return random.choice(
                tuple(  # raises an error if called shortly after start
                    filter(
                        lambda _wq: _wq.rating < 0, WRONG_QUOTES_CACHE.values()
                    )
                )
            ).get_id()
        if rating_filter == "unrated":
            # get a random quote, but filter out already rated quotes
            while (ids := get_random_id()) in WRONG_QUOTES_CACHE:
                if WRONG_QUOTES_CACHE[ids].id == -1:
                    # Check for wrong quotes, that are unrated but in
                    # the cache. They don't have a real wrong_quotes_id
                    return ids
            return ids
        if rating_filter == "rated":
            return random.choice(tuple(WRONG_QUOTES_CACHE.values())).get_id()
        # if rating_filter == "all":
        #     pass
        return get_random_id()

    def on_finish(self):
        """
        Request the data for the next quote, to improve performance.

        This is done to ensure that the data is always up to date.
        """
        quote_id, author_id = self.get_next_id()
        asyncio.run_coroutine_threadsafe(
            get_wrong_quote(quote_id, author_id, use_cache=False),
            asyncio.get_event_loop(),
        )


class QuoteMainPage(QuoteBaseHandler):
    """The main quote page that should render a random quote."""

    async def get(self):
        """Handle the get request to the main quote page and render a quote."""
        quote_id, author_id = self.get_next_id()
        self.redirect(f"/zitate/{quote_id}-{author_id}")


class QuoteById(QuoteBaseHandler):
    """The page with a specified quote that then gets rendered."""

    async def get(self, quote_id: str, author_id: str):
        """Handle the get request to this page and render the quote."""
        await self.render_quote(int(quote_id), int(author_id))

    async def post(self, quote_id_str: str, author_id_str: str):
        """
        Handle the post request to this page and render the quote.

        This is used to vote the quote, without changing the url.
        """
        quote_id = int(quote_id_str)
        author_id = int(author_id_str)
        new_vote_str = self.get_argument("vote", default=None)
        if new_vote_str is None or new_vote_str == "":
            return await self.render_quote(quote_id, author_id)
        if (vote := vote_to_int(new_vote_str)) == new_vote_str:
            return await self.render_quote(quote_id, author_id)

        old_vote = self.get_old_vote(quote_id, author_id)

        self.update_saved_votes(quote_id, author_id, vote)

        # do the voting:
        if vote > old_vote:
            wrong_quote = await create_wq_and_vote(
                1, author_id, quote_id, self.get_hashed_remote_ip()
            )
        elif vote < old_vote:
            wrong_quote = await create_wq_and_vote(
                -1, author_id, quote_id, self.get_hashed_remote_ip()
            )
        else:
            raise HTTPError(500)
        await self.render_wrong_quote(wrong_quote, vote)

    def update_saved_votes(self, quote_id: int, author_id: int, vote: int):
        """Save the new vote in the cookies."""
        wq_str_id = f"{quote_id}-{author_id}"
        vote_dict = self.get_saved_vote_dict()
        if vote == 0:
            del vote_dict[wq_str_id]
        else:
            vote_dict[wq_str_id] = str(vote)
        #  save the votes in a cookie
        self.set_cookie(
            "votes",
            json.dumps(vote_dict),
            expires_days=365,
        )

    async def render_wrong_quote(self, wrong_quote: WrongQuote, vote: int):
        """Render the page with the wrong_quote and this vote."""
        return await self.render(
            "pages/quotes.html",
            wrong_quote=wrong_quote,
            next_href=self.get_next_url(),
            description=str(wrong_quote),
            rating_filter=self.rating_filter(),
            vote=vote,
        )

    async def render_quote(self, quote_id: int, author_id: int):
        """Get and render a wrong quote based on author id and author id."""
        if len(WRONG_QUOTES_CACHE) == 0:
            # should work in a few seconds, the quotes just haven't loaded yet
            self.set_header("Retry-After", "3")
            raise HTTPError(503, reason="Service available in a few seconds")

        return await self.render_wrong_quote(
            await get_wrong_quote(quote_id, author_id),
            self.get_old_vote(quote_id, author_id),
        )

    @cache
    def get_old_vote(self, quote_id: int, author_id: int) -> Literal[-1, 0, 1]:
        """Get the vote saved in the cookie."""
        vote_dict = self.get_saved_vote_dict()

        key = f"{quote_id}-{author_id}"
        if key not in vote_dict:
            return 0

        if vote_dict[key] == "-1":
            return -1
        if vote_dict[key] == "1":
            return 1
        # zero as default if value is not correct
        return 0

    def get_saved_vote_dict(self) -> dict:
        """Get the vote saved in the cookie."""
        votes = self.get_cookie("votes", default=None)
        if votes is None:
            return {}
        return json.loads(votes)


try:  # TODO: add better fix for tests
    asyncio.run_coroutine_threadsafe(
        start_updating_cache_periodically(), asyncio.get_event_loop()
    )
except RuntimeError:
    pass
