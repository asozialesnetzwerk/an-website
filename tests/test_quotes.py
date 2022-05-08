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

import orjson as json
import pytest

import an_website.quotes.quotes as main_page
from an_website import quotes
from an_website.quotes import create

from . import (
    WRONG_QUOTE_DATA,
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_json_response,
    assert_valid_redirect,
    assert_valid_response,
    check_html_page,
    fetch,
)

assert app and fetch


def patch_stuff() -> quotes.WrongQuote:
    """Patch stuff."""

    async def patch(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        print("Called make_api_request", args, kwargs)
        return None

    # this stops requests to the quote API from happening
    quotes.make_api_request = patch

    return quotes.parse_wrong_quote(WRONG_QUOTE_DATA)


async def test_parsing_wrong_quotes() -> None:
    """Test parsing wrong_quotes."""
    wrong_quote = patch_stuff()

    assert wrong_quote.id == 1
    # quote_id (1) - author_id (2)
    assert wrong_quote.get_id_as_str() == "1-2"
    assert wrong_quote.rating == 4

    # parsing the same dict twice should return the same object twice
    assert id(wrong_quote) == id(quotes.parse_wrong_quote(WRONG_QUOTE_DATA))

    author = quotes.parse_author(WRONG_QUOTE_DATA["author"])  # type: ignore[arg-type]
    assert id(author) == id(wrong_quote.author)
    assert author == await quotes.get_author_by_id(author_id=author.id)
    assert author.name == "Kim Jong-il"
    assert author.id == 2

    quote = quotes.parse_quote(WRONG_QUOTE_DATA["quote"])  # type: ignore[arg-type]
    assert id(quote) == id(wrong_quote.quote)
    assert quote == await quotes.get_quote_by_id(quote_id=quote.id)
    assert quote.id == 1
    assert quote.author.id == 1

    assert await quotes.get_rating_by_id(1, 2) == 4

    assert 1 == len(quotes.QUOTES_CACHE) == quotes.MAX_QUOTES_ID.value
    assert 2 == len(quotes.AUTHORS_CACHE) == quotes.MAX_AUTHORS_ID.value


def test_author_updating() -> None:
    """Test updating the author."""
    patch_stuff()

    assert (author := quotes.get_author_updated_with(1, "test")).name == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert author.name == "Abraham Lincoln"


async def test_create() -> None:
    """Test some functions in the quote create module."""
    wrong_quote = patch_stuff()

    assert wrong_quote.quote.author is create.get_author_by_name(
        "Abraham Lincoln"
    )
    assert [wrong_quote.quote.author] == await create.get_authors(
        "Abraham Lincoln"
    )
    assert wrong_quote.quote.author is await create.create_author(
        "Abraham Lincoln"
    )
    assert wrong_quote.quote.author in await create.get_authors("abrah lincoln")

    assert wrong_quote.author is create.get_author_by_name("Kim Jong-il")
    assert wrong_quote.author is create.get_author_by_name("kIm jong-il")
    assert wrong_quote.author is await create.create_author("kIm jong-il")

    assert [wrong_quote.author] == await create.get_authors("kIm jong-il")
    assert wrong_quote.author in await create.get_authors("kIn jon il")

    assert create.get_author_by_name("lol") is None

    quote_str = wrong_quote.quote.quote.lower()

    assert create.get_quote_by_str(quote_str) is wrong_quote.quote
    assert create.get_quote_by_str(quote_str.upper()) is wrong_quote.quote
    assert create.get_quote_by_str(quote_str.title()) is wrong_quote.quote
    assert create.get_quote_by_str(f"„{quote_str}“") is wrong_quote.quote
    assert create.get_quote_by_str(f'"{quote_str}"') is wrong_quote.quote

    assert (
        await create.create_quote(f'"{quote_str}"', None)  # type: ignore[arg-type]
        is wrong_quote.quote
    )

    assert await create.get_quotes(quote_str) == [wrong_quote.quote]

    modified_quote_str = quote_str[1:8] + "x" + quote_str[9:-1].upper()
    assert wrong_quote.quote in await create.get_quotes(modified_quote_str)


async def test_argument_checking_create_pages(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test whether the create handlers complain because of missing args."""
    wrong_quote = patch_stuff()

    await quotes.make_api_request("/test")

    for data in (
        "quote-1=&fake-author-1=",
        "quote-1=test&fake-author-1=",
        "quote-1=&fake-author-1=test",
        "x=y",
    ):
        assert_valid_html_response(
            await fetch("/zitate/erstellen", method="POST", body=data), 400
        )

    for data in (
        "quote-2=&fake-author-2=",
        "quote-2=test&fake-author-2=",
        "quote-2=&fake-author-2=test",
        "x=y",
    ):
        assert_valid_html_response(
            await fetch("/zitate/create-wrong-quote", method="POST", body=data),
            400,
        )

    for num in (1, 2):
        url = "/zitate/erstellen" if num == 1 else "/zitate/create-wrong-quote"
        await assert_valid_redirect(
            fetch,
            url,
            "/zitate/1-1",
            method="POST",
            body=json.dumps(
                {
                    f"quote-{num}": wrong_quote.quote.quote.lower(),
                    f"fake-author-{num}": wrong_quote.quote.author.name.upper(),
                }
            ),
        )
        await assert_valid_redirect(
            fetch,
            url,
            "/zitate/1-2",
            method="POST",
            body=json.dumps(
                {
                    f"quote-{num}": wrong_quote.quote.quote.upper(),
                    f"fake-author-{num}": wrong_quote.author.name.lower(),
                }
            ),
        )


async def test_quote_updating() -> None:
    """Test updating the quote."""
    patch_stuff()

    quote = await quotes.get_quote_by_id(1)

    assert (
        quote.quote == "Frage nicht, was dein Land für dich tun kann, "
        "frage, was du für dein Land tun kannst."
    )
    quote.quote = "test"

    assert quote.quote == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert (
        quote.quote == "Frage nicht, was dein Land für dich tun kann, "
        "frage, was du für dein Land tun kannst."
    )


async def test_quote_request_handlers(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test the request handlers for the quotes page."""
    patch_stuff()  # add data to cache
    await check_html_page(fetch, "/zitate")
    await check_html_page(fetch, "/zitate/1-1")
    await check_html_page(fetch, "/zitate/1-2")

    assert_valid_json_response(await fetch("/api/zitate/1-1"))
    assert_valid_json_response(await fetch("/api/zitate/1-2"))

    await assert_valid_redirect(
        fetch, "/zitate?quote=1&author=1", "/zitate/1-1"
    )
    await assert_valid_redirect(fetch, "/z/1-1", "/zitate/1-1")

    await assert_valid_redirect(fetch, "/z/1", "/zitate/1")
    await assert_valid_redirect(fetch, "/zitate/1", "/zitate/1-2")

    await assert_valid_redirect(fetch, "/zitate?author=1", "/zitate/-1")
    await assert_valid_redirect(fetch, "/z/-1", "/zitate/-1")
    await assert_valid_redirect(fetch, "/zitate/-1", "/zitate/info/a/1")

    await assert_valid_redirect(fetch, "/zitate?quote=1", "/zitate/1-")
    await assert_valid_redirect(fetch, "/z/1-", "/zitate/1-")
    await assert_valid_redirect(fetch, "/zitate/1-", "/zitate/info/z/1")

    for i in (1, 2):
        # twice because we cache the author info from wikipedia
        assert_valid_html_response(await fetch(f"/zitate/info/a/{i}"))
        assert_valid_html_response(await fetch(f"/zitate/info/a/{i}"))

    await check_html_page(fetch, "/zitate/info/z/1")
    await check_html_page(fetch, "/zitate/share/1-1")
    await check_html_page(fetch, "/zitate/erstellen")
    assert not assert_valid_response(
        await fetch("/zitate/info/z/1", method="HEAD"),
        "text/html; charset=UTF-8",
    ).body
    assert not assert_valid_response(
        await fetch("/zitate/share/1-1", method="HEAD"),
        "text/html; charset=UTF-8",
    ).body
    assert not assert_valid_response(
        await fetch("/zitate/erstellen", method="HEAD"),
        "text/html; charset=UTF-8",
    ).body

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
    assert main_page.vote_to_int("-2") == -1
    assert main_page.vote_to_int("-3") == -1

    assert main_page.vote_to_int("0") == 0
    assert main_page.vote_to_int("00") == 0
    assert main_page.vote_to_int("") == 0
    assert main_page.vote_to_int(None) == 0  # type: ignore[arg-type]

    assert main_page.vote_to_int("1") == 1
    assert main_page.vote_to_int("2") == 1
    assert main_page.vote_to_int("3") == 1

    with pytest.raises(ValueError):
        main_page.vote_to_int("x")


async def test_quote_apis(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test the quote APIs."""
    wrong_quote = patch_stuff()

    response = assert_valid_json_response(
        await fetch(f"/api/zitate/{wrong_quote.get_id_as_str()}")
    )
    assert response["id"] == wrong_quote.get_id_as_str()
    assert response["quote"] == wrong_quote.quote.quote
    assert response["author"] == wrong_quote.author.name
    assert response["real_author"] == wrong_quote.quote.author.name
    assert response["real_author_id"] == wrong_quote.quote.author.id
    assert int(response["rating"]) == wrong_quote.rating

    response = assert_valid_json_response(
        await fetch(f"/api/zitate/{wrong_quote.get_id_as_str()}/full")
    )
    assert response["wrong_quote"] == wrong_quote.to_json()
    response = response["wrong_quote"]
    assert response["id"] == wrong_quote.get_id_as_str()
    assert response["quote"] == wrong_quote.quote.to_json()
    assert response["author"] == wrong_quote.author.to_json()
    assert response["path"] == f"/zitate/{wrong_quote.get_id_as_str()}"
    assert int(response["rating"]) == wrong_quote.rating

    for count in (6, 2, 1):
        response = assert_valid_json_response(
            await fetch(f"/api/zitate/generator?count={count}")
        )
        assert 0 < len(response["quotes"]) <= count
        assert 0 < len(response["authors"]) <= count

        for quote in response["quotes"]:
            assert quote == quotes.QUOTES_CACHE[quote["id"]].to_json()

        for author in response["authors"]:
            assert author == quotes.AUTHORS_CACHE[author["id"]].to_json()
