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

"""The tests for the troet page."""

from __future__ import annotations

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_redirect,
    fetch,
)
from .test_settings import parse_cookie


async def test_troet_page(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the troet page."""
    assert_valid_html_response(await fetch("/troet"))

    for save in ("sure", "nope"):
        response = assert_valid_html_response(
            await fetch(f"/troet?text=xyz&save={save}")
        )
        assert response.request.url == response.effective_url
        assert b'<textarea name="text">xyz</textarea>' in response.body
        assert "Set-Cookie" not in response.headers

    response = assert_valid_html_response(
        await fetch("/troet?instance=http://example.invalid&save=nope")
    )
    assert response.request.url == response.effective_url
    assert b'value="http://example.invalid"' in response.body
    assert "Set-Cookie" not in response.headers

    response = assert_valid_html_response(
        await fetch("/troet?instance=example.test&save=sure")
    )
    assert response.request.url == response.effective_url
    assert b'value="https://example.test"' in response.body
    assert "Set-Cookie" in response.headers
    cookies = response.headers.get_list("Set-Cookie")
    assert cookies and len(cookies) == 1
    cookie = parse_cookie(cookies[0])
    assert len(cookie) == 1
    morsel = cookie[tuple(cookie)[0]]
    assert morsel["expires"]
    assert morsel["path"] == "/troet"
    assert morsel["samesite"] == "Strict"
    assert morsel.key == "mastodon-instance"
    assert morsel.value == "https://example.test"

    await assert_valid_redirect(
        fetch,
        "/troet?text=xyz",
        "https://example.test/share?text=xyz",
        {307},
        headers={"Cookie": cookies[0]},
    )
    await assert_valid_redirect(
        fetch,
        "/troet?text=xyz%20123",
        "https://example.test/share?text=xyz+123",
        {307},
        headers={"Cookie": cookies[0]},
    )
