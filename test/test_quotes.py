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

"""The tests for the quotes pages."""

from __future__ import annotations

import an_website.quotes.quotes as main_page
from an_website import quotes

from . import (
    WRONG_QUOTE_DATA,
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_json_response,
    assert_valid_redirect,
    assert_valid_response,
    fetch,
)

assert app and fetch


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
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test the request handlers for the quotes page."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)  # add data to cache
    assert_valid_html_response(await fetch("/zitate"))
    assert_valid_html_response(await fetch("/zitate/1-1"))
    assert_valid_html_response(await fetch("/zitate/1-2"))
    assert_valid_json_response(await fetch("/api/zitate/1-1"))
    assert_valid_json_response(await fetch("/api/zitate/1-2"))

    assert_valid_html_response(
        assert_valid_redirect(await fetch("/z/1-1"), "/zitate/1-1")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("/z/1"), "/zitate/1-2")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("/z/-1"), "/zitate/info/a/1")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("/z/1-"), "/zitate/info/z/1")
    )

    for i in (1, 2):
        # twice because we cache the author info from wikipedia
        assert_valid_html_response(await fetch(f"/zitate/info/a/{i}"))
        assert_valid_html_response(await fetch(f"/zitate/info/a/{i}"))

    assert_valid_html_response(await fetch("/zitate/info/z/1"))
    assert_valid_html_response(await fetch("/zitate/share/1-1"))
    assert_valid_html_response(await fetch("/zitate/erstellen"))

    assert len(
        assert_valid_response(await fetch("/zitate/1-1.gif"), "image/gif").body
    ) > len(
        assert_valid_response(
            await fetch("/zitate/1-1.gif?small=sure"), "image/gif"
        ).body
    )
    # pylint: disable=import-outside-toplevel
    from an_website.quotes.quotes_image import FILE_EXTENSIONS

    for extension, name in FILE_EXTENSIONS.items():
        content_type = f"image/{name}"
        assert_valid_response(
            await fetch(f"/zitate/1-1.{extension}"), content_type
        )
        assert_valid_response(
            await fetch(f"/zitate/1-1.{extension.upper()}"), content_type
        )
        assert_valid_response(
            await fetch(f"/zitate/1-2.{extension}"), content_type
        )


def test_parsing_vote_str() -> None:
    """Test parsing vote str."""
    # pylint: disable=compare-to-zero
    assert main_page.vote_to_int("-1") == -1
    assert main_page.vote_to_int("0") == 0
    assert main_page.vote_to_int("1") == 1
