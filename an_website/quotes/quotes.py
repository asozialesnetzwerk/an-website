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

from dataclasses import dataclass

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

    def __str__(self):
        """Return the name of the author."""
        return self.name


@dataclass
class Quote(QuotesObjBase):
    """The quote object with a quote text and an author."""

    quote: str
    author: Author

    def __str__(self):
        """Return the the content of the quote."""
        return self.quote


@dataclass
class WrongQuote:
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


async def get_quote_by_id(quote_id: int) -> Quote:
    """Get a quote by its id."""
    if quote_id in QUOTES_CACHE:
        return QUOTES_CACHE[quote_id]
    # TODO: do db query here
    return Quote(quote_id, f"Hallo {quote_id}", Author(1, "Autor"))


async def get_author_by_id(author_id: int) -> Author:
    """Get an author by its id."""
    if author_id in AUTHORS_CACHE:
        return AUTHORS_CACHE[author_id]
    # TODO: do db query here
    return Author(author_id, f"Frau {author_id}")


async def get_rating_by_id(quote_id: int, author_id: int) -> int:
    """Get the rating of a wrong quote."""
    wrong_quote_id = (quote_id, author_id)
    if wrong_quote_id in WRONG_QUOTES_CACHE:
        return WRONG_QUOTES_CACHE[wrong_quote_id].rating
    # TODO: do db query here
    return 0


async def get_wrong_quote(quote_id: int, author_id: int) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    wrong_quote_id = (quote_id, author_id)
    if wrong_quote_id in WRONG_QUOTES_CACHE:
        return WRONG_QUOTES_CACHE[wrong_quote_id]
    wrong_quote = WrongQuote(
        quote=await get_quote_by_id(quote_id),
        author=await get_author_by_id(author_id),
        rating=await get_rating_by_id(quote_id, author_id),
    )
    WRONG_QUOTES_CACHE[wrong_quote_id] = wrong_quote
    return wrong_quote


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
