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

"""A page to create new wrong quotes."""

from __future__ import annotations

import logging

from Levenshtein import distance  # type: ignore
from tornado.web import HTTPError

from ..utils.utils import ModuleInfo
from . import (
    AUTHORS_CACHE,
    QUOTES_CACHE,
    Author,
    Quote,
    QuoteReadyCheckHandler,
    fix_quote_str,
    make_api_request,
    parse_author,
    parse_quote,
)

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate/erstellen", CreatePage1),
            (r"/zitate/create-wrong-quote", CreatePage2),
        ),
        name="Falsche-Zitate-Ersteller",
        description="Erstelle witzige falsch zugeordnete Zitate",
        aliases=("/zitate/create",),
        path="/zitate/erstellen",
        hidden=True,
    )


async def create_quote(quote_str: str, author: Author) -> Quote:
    """Create a quote."""
    quote_str = fix_quote_str(quote_str)

    quote = get_quote_by_str(quote_str)
    if quote is not None:
        return quote

    return parse_quote(
        await make_api_request(
            "quotes",
            method="POST",
            body=f"author={author.id}&quote={quote_str}",
        )
    )


async def create_author(author_str: str) -> Author:
    """Create an author."""
    author_str = author_str.strip()

    author = get_author_by_name(author_str)
    if author is not None:
        return author

    return parse_author(
        await make_api_request(
            "authors", method="POST", body=f"author={author_str}"
        )
    )


async def create_wrong_quote(
    real_author_param: Author | str,
    fake_author_param: Author | str,
    quote_param: Quote | str,
) -> str:
    """Create a wrong quote and return the id in the q_id-a_id format."""
    if isinstance(fake_author_param, str):
        if not fake_author_param:
            raise HTTPError(400, "Fake author is needed, but empty.")
        fake_author = await create_author(fake_author_param)
    else:
        fake_author = fake_author_param

    if isinstance(quote_param, str):
        if not quote_param:
            raise HTTPError(400, "Quote is needed, but empty.")

        if isinstance(real_author_param, str):
            if not real_author_param:
                raise HTTPError(400, "Real author is needed, but empty.")
            real_author = await create_author(real_author_param)
        else:
            real_author = real_author_param
        quote = await create_quote(quote_param, real_author)
    else:
        quote = quote_param

    return f"{quote.id}-{fake_author.id}"


async def get_authors(author_name: str) -> list[Author | str]:
    """Get the possible meant authors based on the str."""
    author = get_author_by_name(author_name)
    if author is not None:
        return [author]

    author_name_lower = author_name.lower()
    max_distance = min(5, len(author_name) // 2 + 1)
    authors: list[Author | str] = [
        *(
            _a
            for _a in AUTHORS_CACHE.values()
            if distance(_a.name.lower(), author_name_lower) <= max_distance
        ),
        author_name,
    ]
    # authors should be in most cases title case
    fixed_author = author_name.title()
    if fixed_author not in authors:
        authors.append(fixed_author)
    # no other fixes for authors that are less long
    if len(author_name) < 2:
        return authors
    # maybe only the first letter upper case
    fixed_author_2 = author_name[0].upper() + author_name[1:]
    if fixed_author_2 not in authors:
        authors.append(fixed_author_2)
    return authors


def get_author_by_name(name: str) -> None | Author:
    """Get an author by its name."""
    lower_name = name.lower()
    for _a in AUTHORS_CACHE.values():
        if _a.name.lower() == lower_name:
            return _a
    return None


def get_quote_by_str(quote_str: str) -> None | Quote:
    """Get an author by its name."""
    lower_quote = fix_quote_str(quote_str).lower()
    for _q in QUOTES_CACHE.values():
        if _q.quote.lower() == lower_quote:
            return _q
    return None


async def get_quotes(quote_str: str) -> list[Quote | str]:
    """Get the possible meant authors based on the str."""
    quote: None | Quote = get_quote_by_str(quote_str)
    if isinstance(quote, Quote):
        return [quote]

    lower_quote_str = quote_str.lower()
    max_distance = min(16, len(quote_str) // 2 + 1)
    quotes: list[Quote | str] = [
        *(
            _q
            for _q in QUOTES_CACHE.values()
            if distance(_q.quote.lower(), lower_quote_str) <= max_distance
        ),
        fix_quote_str(quote_str),
    ]
    if not (
        quote_str.endswith("?")
        or quote_str.endswith(".")
        or quote_str.endswith("!")
    ):
        quotes.append(quote_str + ".")
    return quotes


class CreatePage1(QuoteReadyCheckHandler):
    """The request handler for the create page."""

    RATELIMIT_POST_LIMIT = 5
    RATELIMIT_POST_COUNT_PER_PERIOD = 10  # 10 requests per minute

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the create page."""
        if head:
            return
        await self.render(
            "pages/quotes/create1.html",
            quotes=tuple(QUOTES_CACHE.values()),
            authors=tuple(AUTHORS_CACHE.values()),
        )

    async def post(self) -> None:
        """Handle POST requests to the create page."""
        quote_str = self.get_argument("quote-1", default=None)
        fake_author_str = self.get_argument("fake-author-1", default=None)
        if not (quote_str and fake_author_str):
            raise HTTPError(
                400,
                reason=(
                    "Missing arguments. quote-1 and fake-author-1 are needed."
                ),
            )
        assert quote_str and fake_author_str  # for mypy
        quote: None | Quote = get_quote_by_str(quote_str)
        fake_author: None | Author = get_author_by_name(fake_author_str)

        if quote and fake_author:
            # if selected existing quote and existing
            # fake author just redirect to the page of this quote
            return self.redirect(
                self.fix_url(
                    f"/zitate/{quote.id}-{fake_author.id}",
                    as_json=self.get_as_json(),
                ),
            )

        # TODO: Search for real author, to reduce work for users
        real_author_str = self.get_argument("real-author-1", default=None)
        if not real_author_str:
            raise HTTPError(
                400, reason="Missing arguments. real-author-1 is needed."
            )

        quotes: list[Quote | str] = (
            [quote] if quote else await get_quotes(quote_str)
        )
        real_authors: list[Author | str] = (
            [quote.author] if quote else await get_authors(real_author_str)
        )
        fake_authors: list[Author | str] = (
            [fake_author] if fake_author else await get_authors(fake_author_str)
        )

        if 1 == len(quotes) == len(real_authors) == len(fake_authors):
            wq_id = await create_wrong_quote(
                real_authors[0],
                fake_authors[0],
                quotes[0],
            )
            return self.redirect(
                self.fix_url(f"/zitate/{wq_id}", as_json=self.get_as_json())
            )

        await self.render(
            "pages/quotes/create2.html",
            quotes=quotes,
            real_authors=real_authors,
            fake_authors=fake_authors,
        )


class CreatePage2(QuoteReadyCheckHandler):
    """The request handler for the second part of the create page."""

    RATELIMIT_POST_LIMIT = 5
    RATELIMIT_POST_COUNT_PER_PERIOD = 10  # 10 requests per minute

    async def post(self) -> None:
        """Handle POST requests to the create page."""
        quote_str = self.get_argument("quote-2", default=None)
        fake_author_str = self.get_argument("fake-author-2", default=None)

        if not (quote_str and fake_author_str):
            raise HTTPError(
                400,
                reason=(
                    "Missing arguments. quote-2 and fake-author-2 are needed."
                ),
            )

        if (quote := get_quote_by_str(quote_str)) and (
            fake_author := get_author_by_name(fake_author_str)
        ):
            # if selected existing quote and existing
            # fake author just redirect to the page of this quote
            return self.redirect(
                self.fix_url(
                    f"/zitate/{quote.id}-{fake_author.id}",
                    as_json=self.get_as_json(),
                ),
            )

        real_author = self.get_argument("real-author-2", default=None)

        if not real_author:
            raise HTTPError(
                400,
                reason="Missing argument. real-author-2 is required.",
            )

        wq_id = await create_wrong_quote(
            real_author,
            fake_author_str,
            quote_str,
        )
        return self.redirect(
            self.fix_url(f"/zitate/{wq_id}", as_json=self.get_as_json())
        )
