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

"""The tests for the permission system of an-website."""

from __future__ import annotations

import socket

from an_website.utils.utils import Permissions

from . import FetchCallable, app, assert_valid_response, fetch
from .test_backdoor import request_and_parse

assert fetch and app


async def test_permissions(
    # pylint: disable=redefined-outer-name,unused-argument
    fetch: FetchCallable,
    http_server_port: tuple[socket.socket, int],
) -> None:
    """Test stuff with permissions."""
    for key, headers in (
        (
            "",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "s0",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "s1",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "sure",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "s2",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "sure",
            },
        ),
        (
            "s3",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "sure",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "sure",
            },
        ),
        (
            "s4",
            {
                "X-Permission-Backdoor": "sure",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "123qweQWE!@#000000000",
            {
                "X-Permission-Backdoor": "sure",
                "X-Permission-Ratelimits": "sure",
                "X-Permission-Update": "sure",
                "X-Permission-Traceback": "sure",
            },
        ),
    ):
        assert_valid_response(
            await fetch("/api/ping", headers={"Authorization": key}),
            "text/plain; charset=UTF-8",
            200,
            headers=headers,
        )
        assert_valid_response(
            await fetch(f"/api/ping?key={key.replace('#', '%23')}"),
            "text/plain; charset=UTF-8",
            200,
            headers=headers,
        )


async def test_permissions_with_backdoor(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test permissions with the backdoor."""
    response = await request_and_parse(
        fetch, "app.settings['TRUSTED_API_SECRETS'].get('')"
    )
    assert isinstance(response, dict)
    assert response["success"]
    assert not response["output"]
    assert response["result"] is None

    response = await request_and_parse(
        fetch, "app.settings['TRUSTED_API_SECRETS']['123qweQWE!@#000000000']"
    )
    assert isinstance(response, dict)
    assert response["success"]
    assert not response["output"]
    assert response["result"] == (
        "<Permissions.UPDATE|BACKDOOR|TRACEBACK|RATELIMITS: 15>",
        Permissions(15),
    )

    response = await request_and_parse(
        fetch, "len(app.settings['TRUSTED_API_SECRETS'])"
    )
    assert isinstance(response, dict)
    assert response["success"]
    assert not response["output"]
    assert response["result"] == ("6", 6)
