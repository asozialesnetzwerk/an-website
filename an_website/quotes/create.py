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

"""Create-page to create new wrong quotes."""
from __future__ import annotations

import logging
from typing import Optional, Union
from urllib.parse import quote as quote_url

import orjson as json

# pylint: disable=no-name-in-module
from Levenshtein import distance  # type: ignore
from tornado.web import HTTPError

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo
from . import (
    API_URL,
    AUTHORS_CACHE,
    HTTP_CLIENT,
    QUOTES_CACHE,
    Author,
    Quote,
    fix_quote_str,
    parse_author,
    parse_quote,
)

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate/erstellen/", CreatePage),
            (r"/zitate/create-wrong-quote/", CreatePage2),
        ),
        name="Falsch zugeordnete Zitate",
        description="Erstelle witzige falsch zugeordnete Zitate",
        aliases=("/zitate/create/",),
        path="/zitate/erstellen/",
    )


async def create_quote(quote_str: str, author: Author) -> Quote:
    """Create a quote."""
    quote_str = fix_quote_str(quote_str)

    quote = get_quote_by_str(quote_str)
    if quote is not None:
        return quote

    response = await HTTP_CLIENT.fetch(
        f"{API_URL}/quotes",
        raise_error=False,
        method="POST",
        body=f"author={author.id}&quote={quote_url(quote_str)}",
    )
    if response.code != 200:
        raise HTTPError(
            400,
            reason=f"zitate.prapsschnalinen.de returned: {response.reason}",
        )

    return parse_quote(json.loads(response.body))


async def create_author(author_str: str) -> Author:
    """Create an author."""
    author_str = author_str.strip()

    author = get_author_by_name(author_str)
    if author is not None:
        return author

    response = await HTTP_CLIENT.fetch(
        f"{API_URL}/authors",
        raise_error=False,
        method="POST",
        body=f"author={quote_url(author_str)}",
    )
    if response.code != 200:
        raise HTTPError(
            400,
            reason=f"zitate.prapsschnalinen.de returned: {response.reason}",
        )

    return parse_author(json.loads(response.body))


async def create_wrong_quote(
    real_author_param: Union[Author, str],
    fake_author_param: Union[Author, str],
    quote_param: Union[Quote, str],
) -> str:
    """Create a wrong quote and return the id in the q_id-a_id format."""
    if isinstance(real_author_param, str):
        real_author = await create_author(real_author_param)
    else:
        real_author = real_author_param
    if isinstance(fake_author_param, str):
        fake_author = await create_author(fake_author_param)
    else:
        fake_author = fake_author_param
    if isinstance(quote_param, str):
        quote = await create_quote(quote_param, real_author)
    else:
        quote = quote_param
        if quote.author != real_author:
            # pylint: disable=logging-fstring-interpolation
            logger.warning(f"{real_author=} is not the author of {quote=}")

    return f"{quote.id}-{fake_author.id}"


async def get_authors(author_name: str) -> list[Union[Author, str]]:
    """Get the possible meant authors based on the str."""
    author = get_author_by_name(author_name)
    if author is not None:
        return [author]

    authors: list[Union[Author, str]] = [
        *filter(
            lambda _a: distance(_a.name, author_name) < 2,
            AUTHORS_CACHE.values(),
        ),
        author_name,
    ]
    fixed_author = author_name.title()
    if fixed_author not in authors:
        authors.append(fixed_author)
    return authors


def get_author_by_name(name: str) -> Optional[Author]:
    """Get an author by its name."""
    lower_name = name.lower()
    for _a in AUTHORS_CACHE.values():
        if _a.name.lower() == lower_name:
            return _a
    return None


def get_quote_by_str(quote_str: str) -> Optional[Quote]:
    """Get an author by its name."""
    lower_quote = fix_quote_str(quote_str).lower()
    for _q in QUOTES_CACHE.values():
        if _q.quote.lower() == lower_quote:
            return _q
    return None


async def get_quotes(quote_str: str) -> list[Union[Quote, str]]:
    """Get the possible meant authors based on the str."""
    quote: Optional[Quote] = get_quote_by_str(quote_str)
    if isinstance(quote, Quote):
        return [quote]

    quotes: list[Union[Quote, str]] = [
        *filter(
            lambda _q: distance(_q.quote, quote_str) < 4,
            QUOTES_CACHE.values(),
        ),
        fix_quote_str(quote_str),
    ]
    return quotes


class CreatePage(BaseRequestHandler):
    """The request handler for the create page."""

    async def get(self):
        """Handle get requests to the create page."""
        await self.render(
            "pages/quotes/create1.html",
            quotes=tuple(QUOTES_CACHE.values()),
            authors=tuple(AUTHORS_CACHE.values()),
        )

    async def post(self):
        """Handle post requests to the create page."""
        quote_str = self.get_argument("quote-1")
        fake_author_str = self.get_argument("fake-author-1")

        if None not in (
            (quote := get_quote_by_str(quote_str)),
            (fake_author := get_author_by_name(fake_author_str)),
        ):
            # if selected existing quote and existing
            # fake author just redirect to the page of this quote
            return self.redirect(
                self.fix_url(f"/zitate/{quote.id}-{fake_author.id}"),
            )

        # TODO: Search for real author, to reduce work for users
        real_author_str = self.get_argument("real-author-1")

        quotes = await get_quotes(quote_str)
        real_authors = await get_authors(real_author_str)
        fake_authors = await get_authors(fake_author_str)

        if 1 == len(quotes) == len(real_authors) == len(fake_authors):
            _id = await create_wrong_quote(
                real_authors[0],
                fake_authors[0],
                quotes[0],
            )
            return self.redirect(self.fix_url(f"/zitate/{_id}"))

        await self.render(
            "pages/quotes/create2.html",
            quotes=quotes,
            real_authors=real_authors,
            fake_authors=fake_authors,
        )


class CreatePage2(BaseRequestHandler):
    """The request handler for the second part of the create page."""

    async def post(self):
        """Handle post requests to the create page."""
        quote_str = self.get_argument("quote-2")
        fake_author_str = self.get_argument("fake-author-2")

        if None not in (
            (quote := get_quote_by_str(quote_str)),
            (fake_author := get_author_by_name(fake_author_str)),
        ):
            # if selected existing quote and existing
            # fake author just redirect to the page of this quote
            return self.redirect(
                self.fix_url(f"/zitate/{quote.id}-{fake_author.id}"),
            )

        _id = await create_wrong_quote(
            self.get_argument("real-author-2"),
            fake_author_str,
            quote_str,
        )
        return self.redirect(self.fix_url(f"/zitate/{_id}"))
