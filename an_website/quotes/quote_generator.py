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

"""Generate quotes and authors for users to make their own wrong quotes."""

from __future__ import annotations

import random

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo
from . import (
    Author,
    Quote,
    QuoteReadyCheckHandler,
    get_authors,
    get_quotes,
    get_wrong_quotes,
)


def get_module_info(*, hidden: bool = True) -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate/generator", QuoteGenerator),
            (r"/api/zitate/generator", QuoteGeneratorAPI),
        ),
        name="Der Zitate-Generator",
        short_name="Zitate-Generator",
        description="Lasse falsch zugeordnete Zitate generieren",
        path="/zitate/generator",
        keywords=("Generator", "Falsche Zitate", "Falsch zugeordnete Zitate"),
        hidden=hidden,
    )


def get_authors_and_quotes(count: int) -> tuple[list[Author], list[Quote]]:
    """Get random batch of authors and quotes."""
    if count < 1:
        return [], []

    authors: list[Author] = list(get_authors(shuffle=True)[:count])
    quotes: list[Quote] = list(get_quotes(shuffle=True)[:count])

    if len(authors) <= 1 or len(quotes) <= 1:
        return authors, quotes

    wrong_quote = get_wrong_quotes(lambda wq: wq.rating > 0, shuffle=True)[0]

    if wrong_quote.author not in authors:
        authors[random.randrange(0, len(authors))] = wrong_quote.author

    if wrong_quote.quote not in quotes:
        quotes[random.randrange(0, len(quotes))] = wrong_quote.quote

    return authors, quotes


class QuoteGenerator(QuoteReadyCheckHandler):
    """The request handler for the quote generator HTML page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        count = min(10, int(self.get_argument("count", "5") or "5"))
        authors, quotes = get_authors_and_quotes(count)
        if head:
            return
        await self.render(
            "pages/quotes/quote_generator.html", authors=authors, quotes=quotes
        )


class QuoteGeneratorAPI(APIRequestHandler, QuoteReadyCheckHandler):
    """The request handler for the quote generator API."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        count = min(10, int(self.get_argument("count", "5") or "5"))
        authors, quotes = get_authors_and_quotes(count)
        if head:
            return
        await self.finish_dict(
            authors=[author.to_json() for author in authors],
            quotes=[quote.to_json() for quote in quotes],
        )
