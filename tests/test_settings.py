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

from http.cookies import SimpleCookie

import orjson as json

from . import FetchCallable, app, assert_url_query, assert_valid_response, fetch

assert fetch and app


async def test_setting_stuff_without_cookies(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test changing settings with requests without saving to cookie."""
    for request_body in (
        json.dumps(
            {
                "theme": "pink",
                "no_3rd_party": "sure",
                "dynload": "sure",
            }
        ),
        json.dumps(
            {
                "theme": "pink",
                "no_3rd_party": "sure",
                "dynload": "sure",
                "save_in_cookie": "nope",
            }
        ),
        "theme=pink&no_3rd_party=sure&dynload=sure",
        "theme=pink&no_3rd_party=sure&dynload=sure&save_in_cookie=nope",
        "",
    ):
        response = await fetch(
            "/einstellungen"
            if request_body
            else "/einstellungen?theme=pink&no_3rd_party=sure&dynload=sure",
            method="POST",
            body=request_body,
        )
        assert_valid_response(response, content_type="text/html; charset=UTF-8")
        assert_url_query(
            response.effective_url,
            theme="pink",
            no_3rd_party="sure",
            dynload="sure",
            save_in_cookie="nope",
        )


async def test_setting_stuff_and_saving_to_cookies(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test changing settings with requests with saving to cookie."""
    for request_body in (
        json.dumps(
            {
                "theme": "pink",
                "no_3rd_party": "sure",
                "dynload": "sure",
                "save_in_cookie": "sure",
            }
        ),
        "theme=pink&no_3rd_party=sure&dynload=sure&save_in_cookie=sure",
        "",
    ):
        response = await fetch(
            "/einstellungen"
            + (
                "?theme=pink&no_3rd_party=sure&dynload=sure&save_in_cookie=sure"
                if not request_body
                else ""
            ),
            method="POST",
            body=request_body,
        )
        assert_valid_response(response, content_type="text/html; charset=UTF-8")
        if request_body:
            assert response.effective_url.endswith("/einstellungen")

        for cookie_header in response.headers.get_list("Set-Cookie"):
            cookie = SimpleCookie()  # type: ignore[var-annotated]
            cookie.load(cookie_header)
            assert len(cookie) == 1
            morsel = cookie[tuple(cookie)[0]]
            assert morsel["expires"]
            assert morsel["path"] == "/"
            assert morsel["samesite"] == "Strict"
            assert morsel.key in {"theme", "no_3rd_party", "dynload"}
            assert morsel.value == ("pink" if morsel.key == "theme" else "sure")
