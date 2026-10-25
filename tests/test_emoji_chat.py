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

"""Emoji chat."""

from urllib.parse import urlencode

import pytest

from . import (
    REDIS_INFO,
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_json_response,
    fetch,
)

assert app and fetch  # type: ignore[truthy-bool]


async def test_emoji_chat(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test emoji chat."""
    if not REDIS_INFO:
        pytest.skip("no redis available")

    assert_valid_html_response(await fetch("/emoji-chat"), {200})

    response = assert_valid_html_response(
        await fetch(
            "/emoji-chat",
            method="POST",
            body=urlencode(
                {
                    "message": b"\xF0\x9F\x8F\xB3\xE2\x80\x8D\xE2\x9A\xA7".decode()
                }
            ),
        ),
        {200},
    )

    flag = b"\xF0\x9F\x8F\xB3\xEF\xB8\x8F\xE2\x80\x8D\xE2\x9A\xA7\xEF\xB8\x8F"

    assert flag in response.body

    data = assert_valid_json_response(await fetch("/api/emoji-chat"), {200})

    assert data["messages"][-1]["content"][0] == flag.decode()
    assert data["messages"][-1]["content"] == [flag.decode()]
