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

import an_website.quotes as quotes


async def test_parsing_wrong_quotes():
    """Test parsing wrong_quotes."""
    wrong_quote_data = {
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
    wrong_quote = quotes.parse_wrong_quote(wrong_quote_data)
    assert wrong_quote.id == 1
    # quote_id (1) - author_id (2)
    assert wrong_quote.get_id_as_str() == "1-2"
    assert wrong_quote.rating == 4

    author = quotes.parse_author(wrong_quote_data["author"])
    assert id(author) == id(wrong_quote.author)
    assert author == await quotes.get_author_by_id(author_id=author.id)

    quote = quotes.parse_quote(wrong_quote_data["quote"])
    assert id(quote) == id(wrong_quote.quote)
    assert quote == await quotes.get_quote_by_id(quote_id=quote.id)
