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

"""The tests for the request handlers of an-website."""

from __future__ import annotations

import itertools
import urllib.parse
from http.cookies import SimpleCookie
from urllib.parse import urlencode

import orjson as json
from lxml.html.html5parser import HTMLParser

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_url_query,
    assert_valid_response,
    fetch,
)


async def test_setting_stuff_without_cookies(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test changing settings with requests without saving to cookie."""
    for request_body in (
        json.dumps(
            {
                "bumpscosity": "0",
                "theme": "pink",
                "no_3rd_party": "sure",
                "dynload": "sure",
                "openmoji": "img",
            }
        ),
        json.dumps(
            {
                "bumpscosity": "0",
                "theme": "pink",
                "no_3rd_party": "sure",
                "dynload": "sure",
                "openmoji": "img",
                "save_in_cookie": "nope",
            }
        ),
        "theme=pink&no_3rd_party=sure&dynload=sure&openmoji=img&bumpscosity=0",
        (
            "theme=pink&no_3rd_party=s&dynload=s&save_in_cookie=n&openmoji=i"
            "&bumpscosity=0"
        ),
        "",
    ):
        response = await fetch(
            (
                "/einstellungen"
                if request_body
                else (
                    "/einstellungen?theme=pink&no_3rd_party=sure&dynload=sure"
                    "&openmoji=img&bumpscosity=0&save_in_cookie=nope"
                )
            ),
            method="POST" if request_body else "GET",
            headers=(
                {"Content-Type": "application/json"}
                if isinstance(request_body, bytes)
                else None
            ),
            body=request_body or None,
            follow_redirects=True,
        )
        assert_valid_response(response, content_type="text/html;charset=utf-8")

        assert_url_query(
            response.effective_url,
            theme="pink",
            no_3rd_party="sure",
            dynload="sure",
            openmoji="img",
            save_in_cookie="nope",
            bumpscosity="0",
        )

        root = HTMLParser(namespaceHTMLElements=False).parse(response.body)
        home_url = root.xpath("//*[@id='back-to-home']")[0].get("href")

        assert_url_query(
            home_url,
            theme="pink",
            no_3rd_party="sure",
            dynload="sure",
            openmoji="img",
            save_in_cookie=None,
            bumpscosity="0",
        )


def parse_cookie(cookie: str) -> SimpleCookie:
    """Parse a cookie string to a SimpleCookie."""
    simple_cookie = SimpleCookie()
    simple_cookie.load(cookie)
    return simple_cookie


async def test_setting_stuff_and_saving_to_cookies(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test changing settings with requests with saving to cookie."""
    for request_body in (
        json.dumps(
            {
                "theme": "pink",
                "no_3rd_party": "sure",
                "dynload": "sure",
                "save_in_cookie": "sure",
                "openmoji": "img",
                "bumpscosity": "0",
            }
        ),
        "theme=pink&no_3rd_party=s&dynload=s&save_in_cookie=s&openmoji=i&bumpscosity=0",
    ):
        response = await fetch(
            "/einstellungen",
            method="POST",
            headers=(
                {"Content-Type": "application/json"}
                if isinstance(request_body, bytes)
                else None
            ),
            body=request_body,
        )
        if request_body:
            assert_valid_response(
                response, content_type="text/html;charset=utf-8"
            )
        else:
            assert response.headers["Location"].endswith("/einstellungen")

        for cookie_header in response.headers.get_list("Set-Cookie"):
            cookie = parse_cookie(cookie_header)
            assert len(cookie) == 1
            morsel = cookie[tuple(cookie)[0]]
            assert morsel["expires"]
            assert morsel["path"] == "/"
            assert morsel["samesite"] == "Strict"
            assert morsel.key in {
                "advanced_settings",
                "ask_before_leaving",
                "bumpscosity",
                "compat",
                "dynload",
                "effects",
                "no_3rd_party",
                "openmoji",
                "theme",
                "scheme",
            }
            if morsel.key == "theme":
                assert morsel.value == "pink"
            elif morsel.key == "scheme":
                assert morsel.value == "system"
            elif morsel.key == "openmoji":
                assert morsel.value == "img"
            elif morsel.key == "bumpscosity":
                assert morsel.value == "0"
            elif morsel.key in {
                "advanced_settings",
                "compat",
                "ask_before_leaving",
            }:
                assert morsel.value == "nope"
            else:
                assert morsel.value == "sure"


async def test_setting_stuff_and_saving_to_cookies2(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test changing settings with requests with saving to cookie."""
    options: tuple[dict[str, str | None], ...] = (
        {
            "theme": "christmas",
            "no_3rd_party": "nope",
            "dynload": "nope",
            "openmoji": "glyf_colr1",
            "bumpscosity": "76",
            "advanced_settings": "nope",
            "compat": "nope",
            "access_token": "xyzzy",
            "ask_before_leaving": "nope",
            "effects": "nope",
            "scheme": "dark",
        },
        {
            "theme": "pink",
            "no_3rd_party": "sure",
            "dynload": "sure",
            "openmoji": "img",
            "bumpscosity": "0",
            "advanced_settings": None,
            "compat": "sure",
            "ask_before_leaving": "sure",
            "effects": "sure",
            "scheme": "system",
        },
        {
            "bumpscosity": "100",
            "theme": "default",
            "no_3rd_party": "nope",
            "dynload": None,
            "openmoji": "img",
            "advanced_settings": "sure",
            "compat": "nope",
            "ask_before_leaving": "nope",
            "effects": "nope",
            "scheme": "light",
        },
    )
    cookies: list[str | None] = [
        "; ".join([f"{key}={value}" for key, value in data.items()])
        for data in options
    ]
    cookies.append(None)

    for data, req_cookie in itertools.product(options, cookies):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if req_cookie is not None:
            headers["Cookie"] = req_cookie
        response = await fetch(
            "/einstellungen",
            method="POST",
            headers=headers,
            body=urlencode(
                {
                    "save_in_cookie": "sure",
                    **{
                        key: value
                        for key, value in data.items()
                        if value is not None
                    },
                }
            ),
        )
        assert_valid_response(response, content_type="text/html;charset=utf-8")

        root = HTMLParser(namespaceHTMLElements=False).parse(response.body)
        home_url = root.xpath("//*[@id='back-to-home']")[0].get("href")

        if query := urllib.parse.urlsplit(home_url).query:
            raise AssertionError(f"Back to home URL has query: {query}")

        for cookie_header in response.headers.get_list("Set-Cookie"):
            cookie = parse_cookie(cookie_header)
            assert len(cookie) == 1
            morsel = cookie[tuple(cookie)[0]]
            assert morsel["expires"]
            assert morsel["path"] == "/"
            assert morsel["samesite"] == "Strict"
            assert (
                morsel.key in data
            ), f"{morsel.key} not in {list(data.keys())}"
            if morsel.key == "access_token":
                assert morsel.value == "eHl6enk="
            else:
                assert morsel.value == (
                    data[morsel.key] or "nope"
                ), f"{morsel.value} != {data[morsel.key]}"
