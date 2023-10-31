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

from dataclasses import dataclass
from typing import cast

from rapidfuzz.distance.Levenshtein import distance
from tornado.web import HTTPError, MissingArgumentError

from ..utils.data_parsing import parse_args
from .utils import (
    AUTHORS_CACHE,
    QUOTES_CACHE,
    Author,
    Quote,
    QuoteReadyCheckHandler,
    fix_author_name,
    fix_quote_str,
    make_api_request,
    parse_author,
    parse_quote,
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
            body={
                "author": str(author.id),
                "quote": quote_str,
            },
        )
    )


async def create_author(author_str: str) -> Author:
    """Create an author."""
    author_str = fix_author_name(author_str)

    author = get_author_by_name(author_str)
    if author is not None:
        return author

    return parse_author(
        await make_api_request(
            "authors", method="POST", body={"author": author_str}
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
            author
            for author in AUTHORS_CACHE.values()
            if distance(author.name.lower(), author_name_lower) <= max_distance
        ),
        fix_author_name(author_name),
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
    lower_name = fix_author_name(name).lower()
    for author in AUTHORS_CACHE.values():
        if author.name.lower() == lower_name:
            return author
    return None


def get_quote_by_str(quote_str: str) -> None | Quote:
    """Get an author by its name."""
    lower_quote = fix_quote_str(quote_str).lower()
    for quote in QUOTES_CACHE.values():
        if quote.quote.lower() == lower_quote:
            return quote
    return None


async def get_quotes(quote_str: str) -> list[Quote | str]:
    """Get the possible meant quotes based on the str."""
    quote: None | Quote = get_quote_by_str(quote_str)
    if isinstance(quote, Quote):
        return [quote]

    lower_quote_str = quote_str.lower()
    max_distance = min(16, len(quote_str) // 2 + 1)
    quotes: list[Quote | str] = [
        *(
            quote
            for quote in QUOTES_CACHE.values()
            if distance(quote.quote.lower(), lower_quote_str) <= max_distance
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


@dataclass(slots=True, frozen=True)
class QuoteInfoArgs:
    """Class representing a quote id and an author id."""

    quote: int | None = None
    author: int | None = None


class CreatePage1(QuoteReadyCheckHandler):
    """The request handler for the create page."""

    RATELIMIT_POST_LIMIT = 5
    RATELIMIT_POST_COUNT_PER_PERIOD = 10

    @parse_args(type_=QuoteInfoArgs)
    async def get(self, *, args: QuoteInfoArgs, head: bool = False) -> None:
        """Handle GET requests to the create page."""
        if args.quote is not None and args.author is not None:
            return self.redirect(f"/zitate/{args.quote}-{args.author}")

        if head:
            return

        await self.render(
            "pages/quotes/create1.html",
            quotes=tuple(QUOTES_CACHE.values()),
            authors=tuple(AUTHORS_CACHE.values()),
            selected_quote=None
            if args.quote is None
            else QUOTES_CACHE.get(args.quote),
            selected_author=None
            if args.author is None
            else AUTHORS_CACHE.get(args.author),
        )

    async def post(self) -> None:
        """Handle POST requests to the create page."""
        quote_str = self.get_argument("quote-1", None)
        fake_author_str = self.get_argument("fake-author-1", None)
        if not (quote_str and fake_author_str):
            raise HTTPError(
                400,
                reason=(
                    "Missing arguments. quote-1 and fake-author-1 are needed."
                ),
            )
        quote: None | Quote = get_quote_by_str(quote_str)
        fake_author: None | Author = get_author_by_name(fake_author_str)

        if quote and fake_author:
            # if selected existing quote and existing
            # fake author just redirect to the page of this quote
            return self.redirect(
                self.fix_url(f"/zitate/{quote.id}-{fake_author.id}"),
            )

        if not quote:
            # TODO: search for real author, to reduce work for users
            real_author_str = self.get_argument("real-author-1", None)
            if not real_author_str:
                raise HTTPError(
                    400, reason="Missing arguments. real-author-1 is needed."
                )

        quotes: list[Quote | str] = (
            [quote] if quote else await get_quotes(quote_str)
        )
        real_authors: list[Author | str] = (
            [quote.author]
            if quote
            else await get_authors(cast(str, real_author_str))  # type: ignore[possibly-undefined]  # noqa: B950
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
            return self.redirect(self.fix_url(f"/zitate/{wq_id}"))

        await self.render(
            "pages/quotes/create2.html",
            quotes=quotes,
            real_authors=real_authors,
            fake_authors=fake_authors,
        )


class CreatePage2(QuoteReadyCheckHandler):
    """The request handler for the second part of the create page."""

    RATELIMIT_POST_LIMIT = 5
    RATELIMIT_POST_COUNT_PER_PERIOD = 10

    async def post(self) -> None:
        """Handle POST requests to the create page."""
        quote_str = self.get_argument("quote-2", None)
        if not quote_str:
            raise MissingArgumentError("quote-2")
        fake_author_str = self.get_argument("fake-author-2", None)
        if not fake_author_str:
            raise MissingArgumentError("fake-author-2")

        if (quote := get_quote_by_str(quote_str)) and (
            fake_author := get_author_by_name(fake_author_str)
        ):
            # if selected existing quote and existing
            # fake author just redirect to the page of this quote
            return self.redirect(
                self.fix_url(f"/zitate/{quote.id}-{fake_author.id}"),
            )

        real_author = self.get_argument("real-author-2", None)
        if not real_author:
            raise MissingArgumentError("real-author-2")

        wq_id = await create_wrong_quote(
            real_author,
            fake_author_str,
            quote_str,
        )
        return self.redirect(
            self.fix_url(
                f"/zitate/{wq_id}",
            )
        )
