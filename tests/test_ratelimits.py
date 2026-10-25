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

"""Rate the limits."""

from asyncio import sleep

import pytest
from tornado.web import Application

from . import REDIS_INFO, FetchCallable, app, assert_valid_html_response, fetch

assert app and fetch  # type: ignore[truthy-bool]


@pytest.mark.timeout(30)
async def test_ratelimits(
    fetch: FetchCallable,  # noqa: F811
    app: Application,  # noqa: F811
) -> None:
    """Test ratelimits.."""
    if not REDIS_INFO:
        pytest.skip("redis not available")
    if not REDIS_INFO.has_redis_cell:
        pytest.skip("redis-cell not available")

    app.settings["RATELIMITS"] = True

    try:
        while True:  # pylint: disable=while-used
            response = await fetch("/LOLWUT")
            if response.code != 200:
                break
    finally:
        app.settings["RATELIMITS"] = False

    assert_valid_html_response(response, {420, 429})

    await sleep(int(response.headers["Retry-After"]))
    assert_valid_html_response(
        await fetch("/LOLWUT", follow_redirects=True),
        {200},
    )
