from __future__ import annotations

from dataclasses import dataclass

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate/?", QuoteMainPage),
            # {1,10} is too much, but better too much than not enough
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})/?", QuoteById),
        ),
        name="Falsch zugeordnete Zitate",
        description="Eine Website mit falsch zugeordneten Zitaten",
        path="/zitate",
    )


@dataclass
class QuotesObjBase:
    id: int  # pylint: disable=invalid-name

    def get_id_as_str(self):
        return str(self.id)

    def __str__(self):
        """Return a basic string with the id."""
        return f"QuotesObj({self.id})"


@dataclass
class Author(QuotesObjBase):
    name: str

    def __str__(self):
        """Return the name of the author."""
        return self.name


@dataclass
class Quote(QuotesObjBase):
    quote: str
    author: Author

    def __str__(self):
        """Return the the content of the quote."""
        return self.quote


@dataclass
class WrongQuote(QuotesObjBase):
    quote: Quote
    author: Author
    rating: int

    def get_id_as_str(self):
        return f"{self.quote.id}-{self.author.id}"

    def __str__(self):
        r"""
        Return the wrong quote.

        like: '»quote«\n - author'.
        """
        return f"»{self.quote}«\n - {self.author}"


API_URL: str = "https://zitate.prapsschnalinen.de/api"


async def get_quote_by_id(quote_id: int) -> Quote:
    # do db query here
    return Quote(quote_id, f"Hallo {quote_id}", Author(1, "Autor"))


async def get_author_by_id(author_id: int) -> Author:
    # do db query here
    return Author(author_id, f"Frau {author_id}")


async def get_wrong_quote(quote_id: int, author_id: int) -> WrongQuote:
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
    async def render_quote(self, quote_id: int, author_id: int):
        return await self.render(
            "pages/quotes.html",
            wrong_quote=await get_wrong_quote(quote_id, author_id),
            next_href=f"/zitate/{await self.get_next_id()}",
        )

    async def get_next_id(self):
        return "0-0"


class QuoteMainPage(QuoteBaseHandler):
    async def get(self):
        await self.render_quote(-1, -1)


class QuoteById(QuoteBaseHandler):
    async def get(self, quote_id: str, author_id: str):
        await self.render_quote(int(quote_id), int(author_id))
