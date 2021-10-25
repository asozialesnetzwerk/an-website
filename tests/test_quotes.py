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

"""The module with all the tests for the quotes module."""

from __future__ import annotations

import an_website.quotes.quotes as main_page
from an_website import quotes

WRONG_QUOTE_DATA = {
    # https://zitate.prapsschnalinen.de/api/wrongquotes/1
    "id": 1,
    "author": {
        "id": 2,
        "author": "Kim Jong-il",
    },
    "quote": {
        "id": 1,
        "author": {
            "id": 1,
            "author": "Abraham Lincoln",
        },
        "quote": "Frage nicht, was dein Land für dich tun kann, "
        "frage was du für dein Land tun kannst.",
    },
    "rating": 4,
    "showed": 216,
    "voted": 129,
}


async def test_parsing_wrong_quotes():
    """Test parsing wrong_quotes."""
    wrong_quote = quotes.parse_wrong_quote(WRONG_QUOTE_DATA)
    assert wrong_quote.id == 1
    # quote_id (1) - author_id (2)
    assert wrong_quote.get_id_as_str() == "1-2"
    assert wrong_quote.rating == 4

    # parsing the same dict twice should return the same object twice
    assert id(wrong_quote) == id(quotes.parse_wrong_quote(WRONG_QUOTE_DATA))

    author = quotes.parse_author(WRONG_QUOTE_DATA["author"])
    assert id(author) == id(wrong_quote.author)
    assert author == await quotes.get_author_by_id(author_id=author.id)
    assert author.name == "Kim Jong-il"
    assert author.id == 2

    quote = quotes.parse_quote(WRONG_QUOTE_DATA["quote"])
    assert id(quote) == id(wrong_quote.quote)
    assert quote == await quotes.get_quote_by_id(quote_id=quote.id)
    assert quote.id == 1
    assert quote.author.id == 1

    assert await quotes.get_rating_by_id(1, 2) == 4

    assert 1 == len(quotes.QUOTES_CACHE) == quotes.MAX_QUOTES_ID[0]
    assert 2 == len(quotes.AUTHORS_CACHE) == quotes.MAX_AUTHORS_ID[0]


def test_author_updating():
    """Test updating the author."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert (author := quotes.get_author_updated_with(1, "test")).name == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert author.name == "Abraham Lincoln"


async def test_quote_updating():
    """Test updating the quote."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    quote = await quotes.get_quote_by_id(1)

    assert quote.quote == (
        "Frage nicht, was dein Land für dich tun kann, "
        "frage was du für dein Land tun kannst."
    )
    quote.quote = "test"

    assert quote.quote == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert quote.quote == (
        "Frage nicht, was dein Land für dich tun kann, "
        "frage was du für dein Land tun kannst."
    )


def test_parsing_vote_str():
    """Test parsing vote str."""
    assert main_page.vote_to_int("-1") == -1
    assert main_page.vote_to_int("0") == 0
    assert main_page.vote_to_int("1") == 1
