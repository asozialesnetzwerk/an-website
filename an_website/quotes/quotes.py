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

import orjson as json
from dataclasses import dataclass

from tornado.httpclient import AsyncHTTPClient

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo


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
        return self.name


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
        return self.quote


@dataclass
class WrongQuote(QuotesObjBase):
    """The wrong quote object with a quote, an author and a rating."""

    quote: Quote
    author: Author
    rating: int

    def get_id_as_str(self):
        """
        Get the id of the wrong quote as a string.

        Format: quote_id-author_id
        """
        return f"{self.quote.id}-{self.author.id}"

    def __str__(self):
        """
        Return the wrong quote.

        like: '»quote«\n - author'.
        """
        return f"»{self.quote}«\n - {self.author}"


API_URL: str = "https://zitate.prapsschnalinen.de/api/"

QUOTES_CACHE: dict[int, Quote] = {}
AUTHORS_CACHE: dict[int, Author] = {}
WRONG_QUOTES_CACHE: dict[tuple[int, int], WrongQuote] = {}


async def make_api_request(end_point: str, args: str = "") -> dict:
    """Make api request and return the result as dict."""
    http_client = AsyncHTTPClient()
    print(f"{API_URL}{end_point}?{args}")
    response = await http_client.fetch(
        f"{API_URL}{end_point}?{args}", raise_error=True
    )
    print(response.body)
    return json.loads(response.body)


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


async def get_wrong_quote(quote_id: int, author_id: int) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    wrong_quote_id = (quote_id, author_id)
    wrong_quote = WRONG_QUOTES_CACHE.get(wrong_quote_id, None)
    if wrong_quote is not None:
        return wrong_quote
    wrong_quote = parse_wrong_quote(
        (
            await make_api_request(
                "wrongquotes",
                f"quote_id={quote_id}&autor_id={author_id}&simulate=true",
            )
        )[0]
    )
    WRONG_QUOTES_CACHE[wrong_quote_id] = wrong_quote
    return wrong_quote


def parse_wrong_quote(json_data: dict) -> WrongQuote:
    """Parse a quote"""
    id_tuple = (json_data["quote"]["id"], json_data["author"]["id"])
    rating = json_data["rating"]
    wrong_quote = WRONG_QUOTES_CACHE.setdefault(
        id_tuple,
        WrongQuote(
            id=json_data["id"],
            quote=parse_quote(json_data["quote"]),
            author=parse_author(json_data["author"]),
            rating=rating,
        ),
    )
    if wrong_quote.rating != rating:
        wrong_quote.rating = rating
    return wrong_quote


async def get_rating_by_id(quote_id: int, author_id: int) -> int:
    """Get the rating of a wrong quote."""
    return (await get_wrong_quote(quote_id, author_id)).rating


class QuoteBaseHandler(BaseRequestHandler):
    """The base request handler for the quotes package."""

    async def render_quote(self, quote_id: int, author_id: int):
        """Get and render a wrong quote based on author id and author id."""
        return await self.render(
            "pages/quotes.html",
            wrong_quote=await get_wrong_quote(quote_id, author_id),
            next_href=f"/zitate/{await self.get_next_id()}",
        )

    async def get_next_id(self):  # pylint: disable=R0201
        """Get the id of the next quote."""
        return "0-0"


class QuoteMainPage(QuoteBaseHandler):
    """The main quote page that should render a random quote."""

    async def get(self):
        """Handle the get request to the main quote page and render a quote."""
        await self.render_quote(-1, -1)


class QuoteById(QuoteBaseHandler):
    """The page with a specified quote that then gets rendered."""

    async def get(self, quote_id: str, author_id: str):
        """Handle the get request to this page and render the quote."""
        await self.render_quote(int(quote_id), int(author_id))
