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

import pytest
import tornado.simple_httpclient
import tornado.web

import an_website.quotes.quotes as main_page
from an_website import main, quotes

from . import assert_valid_html_response, assert_valid_json_response


@pytest.fixture
def app() -> tornado.web.Application:
    """Create the application."""
    return main.make_app()


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
        "frage, was du für dein Land tun kannst.",
    },
    "rating": 4,
    "showed": 216,
    "voted": 129,
}


async def test_parsing_wrong_quotes() -> None:
    """Test parsing wrong_quotes."""
    wrong_quote = quotes.parse_wrong_quote(WRONG_QUOTE_DATA)
    assert wrong_quote.id == 1
    # quote_id (1) - author_id (2)
    assert wrong_quote.get_id_as_str() == "1-2"
    assert wrong_quote.rating == 4

    # parsing the same dict twice should return the same object twice
    assert id(wrong_quote) == id(quotes.parse_wrong_quote(WRONG_QUOTE_DATA))

    author = quotes.parse_author(WRONG_QUOTE_DATA["author"])  # type: ignore
    assert id(author) == id(wrong_quote.author)
    assert author == await quotes.get_author_by_id(author_id=author.id)
    assert author.name == "Kim Jong-il"
    assert author.id == 2

    quote = quotes.parse_quote(WRONG_QUOTE_DATA["quote"])  # type: ignore
    assert id(quote) == id(wrong_quote.quote)
    assert quote == await quotes.get_quote_by_id(quote_id=quote.id)
    assert quote.id == 1
    assert quote.author.id == 1

    assert await quotes.get_rating_by_id(1, 2) == 4

    assert 1 == len(quotes.QUOTES_CACHE) == quotes.MAX_QUOTES_ID[0]
    assert 2 == len(quotes.AUTHORS_CACHE) == quotes.MAX_AUTHORS_ID[0]


def test_author_updating() -> None:
    """Test updating the author."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert (author := quotes.get_author_updated_with(1, "test")).name == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert author.name == "Abraham Lincoln"


async def test_quote_updating() -> None:
    """Test updating the quote."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    quote = await quotes.get_quote_by_id(1)

    assert quote.quote == (
        "Frage nicht, was dein Land für dich tun kann, "
        "frage, was du für dein Land tun kannst."
    )
    quote.quote = "test"

    assert quote.quote == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert quote.quote == (
        "Frage nicht, was dein Land für dich tun kann, "
        "frage, was du für dein Land tun kannst."
    )


async def test_quote_request_handlers(
    http_server_client: tornado.simple_httpclient.SimpleAsyncHTTPClient,
) -> None:
    """Test the request handlers for the quotes page."""
    fetch = http_server_client.fetch

    assert_valid_html_response(await fetch("/zitate"))
    assert_valid_html_response(await fetch("/zitate/1-1"))
    assert_valid_json_response(await fetch("/api/zitate/1-2"))
    for i in (1, 2):
        # twice because we cache the author info from wikipedia
        assert_valid_html_response(await fetch(f"/zitate/info/a/{i}"))
        assert_valid_html_response(await fetch(f"/zitate/info/a/{i}"))

    assert_valid_html_response(await fetch("/zitate/info/z/1"))
    assert_valid_html_response(await fetch("/zitate/share/1-1"))
    assert_valid_html_response(await fetch("/zitate/erstellen"))

    response = await fetch("/zitate/1-1/image.gif")
    assert response.code == 200
    # pylint: disable=import-outside-toplevel
    from an_website.quotes.quotes_img import FILE_EXTENSIONS

    for _e in FILE_EXTENSIONS:
        response = await fetch(f"/zitate/1-1/image.{_e}")
        assert response.code == 200
        response = await fetch(f"/zitate/1-1/image.{_e.upper()}")
        assert response.code == 200
        response = await fetch(f"/zitate/1-2/image.{_e}")
        assert response.code == 200


def test_parsing_vote_str() -> None:
    """Test parsing vote str."""
    # pylint: disable=compare-to-zero
    assert main_page.vote_to_int("-1") == -1
    assert main_page.vote_to_int("0") == 0
    assert main_page.vote_to_int("1") == 1
