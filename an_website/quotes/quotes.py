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
        r"""
        Return the wrong quote.

        like: '»quote«\n - author'.
        """
        return f"»{self.quote}«\n - {self.author}"


API_URL: str = "https://zitate.prapsschnalinen.de/api"


async def get_quote_by_id(quote_id: int) -> Quote:
    """Get a quote by its id."""
    # do db query here
    return Quote(quote_id, f"Hallo {quote_id}", Author(1, "Autor"))


async def get_author_by_id(author_id: int) -> Author:
    """Get an author by its id."""
    # do db query here
    return Author(author_id, f"Frau {author_id}")


async def get_wrong_quote(quote_id: int, author_id: int) -> WrongQuote:
    """Get a wrong quote with a quote id and an author id."""
    return WrongQuote(
        id=quote_id * 10_000 + author_id,
        quote=Quote(
            id=quote_id,
            quote=f"Quote({quote_id})",
            author=Author(id=quote_id + 13, name=f"Author({quote_id + 13})"),
        ),
        author=Author(id=author_id, name=f"Author({author_id})"),
        rating=quote_id - author_id,
    )


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
