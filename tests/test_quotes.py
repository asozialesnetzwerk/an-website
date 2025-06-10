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

import urllib.parse
from datetime import datetime, timezone as tz
from functools import cache
from io import BytesIO

import orjson as json
import qoi_rs
from PIL import Image

from an_website.quotes import create, utils as quotes
from an_website.quotes.image import CONTENT_TYPES, FILE_EXTENSIONS

from . import (  # noqa: F401  # pylint: disable=unused-import
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


@cache
def get_wrong_quote() -> quotes.WrongQuote:
    """Patch stuff."""
    return quotes.parse_wrong_quote(WRONG_QUOTE_DATA)


async def test_parsing_wrong_quotes() -> None:
    """Test parsing wrong_quotes."""
    wrong_quote = get_wrong_quote()

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

    assert len(quotes.QUOTES_CACHE) == 1
    assert quotes.MAX_QUOTES_ID.value == 1
    assert len(quotes.AUTHORS_CACHE) == 2
    assert quotes.MAX_AUTHORS_ID.value == 2


def test_author_updating() -> None:
    """Test updating the author."""
    get_wrong_quote()

    assert (
        author := quotes.parse_author({"id": 1, "author": "test"})
    ).name == "test"

    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)

    assert author.name == "Abraham Lincoln"


async def test_create() -> None:
    """Test some functions in the quote create module."""
    wrong_quote = get_wrong_quote()

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

    assert (
        await create.create_quote(
            f'"{quote_str}"',  # noqa: B907
            None,  # type: ignore[arg-type]
        )
        is wrong_quote.quote
    )

    assert await create.get_quotes(quote_str) == [wrong_quote.quote]

    modified_quote_str = quote_str[1:8] + "x" + quote_str[9:-1].upper()
    assert wrong_quote.quote in await create.get_quotes(modified_quote_str)


async def test_argument_checking_create_pages(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test whether the create handlers complain because of missing args."""
    wrong_quote = get_wrong_quote()

    await quotes.make_api_request("/test", entity_should_exist=False)

    for data in (
        "quote-1=&fake-author-1=",
        "quote-1=test&fake-author-1=",
        "quote-1=&fake-author-1=test",
        "x=y",
    ):
        assert_valid_html_response(
            await fetch("/zitate/erstellen", method="POST", body=data), {400}
        )

    for data in (
        "quote-2=&fake-author-2=",
        "quote-2=test&fake-author-2=",
        "quote-2=&fake-author-2=test",
        "x=y",
    ):
        assert_valid_html_response(
            await fetch("/zitate/create-wrong-quote", method="POST", body=data),
            {400},
        )

    for num in (1, 2):
        url = "/zitate/erstellen" if num == 1 else "/zitate/create-wrong-quote"
        await assert_valid_redirect(
            fetch,
            url,
            "/zitate/1-1",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    f"quote-{num}": wrong_quote.quote.quote.lower(),
                    f"fake-author-{num}": wrong_quote.quote.author.name.upper(),
                }
            ),
            codes={303},
        )
        await assert_valid_redirect(
            fetch,
            url,
            "/zitate/1-2",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    f"quote-{num}": wrong_quote.quote.quote.upper(),
                    f"fake-author-{num}": wrong_quote.author.name.lower(),
                }
            ),
            codes={303},
        )


async def test_quote_updating() -> None:
    """Test updating the quote."""
    get_wrong_quote()

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
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test the request handlers for the quotes page."""
    get_wrong_quote()  # add data to cache
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
        "text/html;charset=utf-8",
    ).body
    assert not assert_valid_response(
        await fetch("/zitate/share/1-1", method="HEAD"),
        "text/html;charset=utf-8",
    ).body
    assert not assert_valid_response(
        await fetch("/zitate/erstellen", method="HEAD"),
        "text/html;charset=utf-8",
    ).body

    assert len(
        assert_valid_response(await fetch("/zitate/1-1.gif"), "image/gif").body
    ) > len(
        assert_valid_response(
            await fetch("/zitate/1-1.gif?small=sure"), "image/gif"
        ).body
    )


async def test_quote_image_handlers(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Text downloading quotes as images."""
    for ext, name in FILE_EXTENSIONS.items():
        content_type = CONTENT_TYPES[name]
        image1 = assert_valid_response(
            await fetch(f"/zitate/1-1.{ext}"), content_type
        ).body
        image2 = assert_valid_response(
            await fetch("/zitate/1-1", headers={"Accept": content_type}),
            content_type,
        ).body
        image3 = assert_valid_response(
            await fetch("/api/zitate/1-1", headers={"Accept": content_type}),
            content_type,
        ).body
        if name == "txt":
            assert image1 == image3
        else:
            image4 = assert_valid_response(
                await fetch(
                    "/zitate/1-1/image", headers={"Accept": content_type}
                ),
                content_type,
            ).body
            if name == "xlsx":
                continue
            assert image1 == image2 == image3 == image4
            if name == "pdf":
                continue
            img = Image.open(BytesIO(image4), formats=[name])
            try:  # pylint: disable=too-many-try-statements
                img.load()
                assert img.width == 1000
                assert img.height == 750
                if name == "gif":
                    assert img.getpixel((0, 0)) == 255
                elif name == "spider":
                    assert not img.getpixel((0, 0))
                else:
                    assert img.getpixel((0, 0)) == (0, 0, 0), f"{name}"
                if ext == "qoi":
                    img2 = qoi_rs.decode_pillow(image4)
                    assert tuple(img.getdata()) == tuple(img2.getdata())
                    img2.close()
                    qimg = qoi_rs.decode(image4)
                    assert qimg.mode == "RGB"
                    assert qimg.width == 1000
                    assert qimg.height == 750
            finally:
                img.close()


async def test_quote_redirect_api(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the quote redirect API."""
    response = await fetch(
        "/api/zitate?show-rating=s&r=all", follow_redirects=True
    )
    url = urllib.parse.urlsplit(response.effective_url)
    assert "show-rating=sure" in url.query
    assert "r=all" in url.query
    json_ = assert_valid_json_response(response)
    assert url.path == f"/api/zitate/{json_['id']}"
    assert json_["rating"] != "???"


async def test_quote_apis(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the quote APIs."""
    wrong_quote = get_wrong_quote()
    today = datetime.now(tz=tz.utc).date()

    response = assert_valid_json_response(
        await fetch(f"/api/zitate/{wrong_quote.get_id_as_str()}?show-rating=s")
    )
    if (today.month, today.day) != (4, 1):
        assert response["id"] == wrong_quote.get_id_as_str()
        assert response["quote"] == wrong_quote.quote.quote
        assert response["author"] == wrong_quote.author.name
        assert response["real_author"] == wrong_quote.quote.author.name
        assert response["real_author_id"] == wrong_quote.quote.author.id
        assert int(response["rating"]) == wrong_quote.rating

    response = assert_valid_json_response(
        await fetch(
            f"/api/zitate/{wrong_quote.get_id_as_str()}/full?show-rating=sure"
        )
    )
    if (today.month, today.day) != (4, 1):
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
