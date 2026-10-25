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

"""LOLWUT?."""

from urllib.parse import urlparse

import pytest

from . import REDIS_INFO, FetchCallable, app, assert_valid_html_response, fetch

assert app and fetch  # type: ignore[truthy-bool]


async def test_lolwut(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test LOLWUT."""
    codes: set[int] = {200} if REDIS_INFO else {503}
    response = await fetch("/lolwut/", follow_redirects=True)
    response = assert_valid_html_response(response, codes)
    assert response.effective_url.endswith("/LOLWUT")


async def test_lolwut_with_working_redis(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test LOLWUT."""
    if not REDIS_INFO:
        pytest.skip("no redis available")

    for url in (
        *(f"/lolWUT/{i}/" for i in range(1, 11)),
        "/lolwut/8/it/",
        "/lolwut/8/IT/",
        "/LOLWUT/6/10/5/4",
    ):
        response = await fetch(url, follow_redirects=True)
        response = assert_valid_html_response(response, {200})
        path = urlparse(response.effective_url).path
        assert path.startswith("/LOLWUT"), f"{path!r} should be LOLWUT"
        assert path.isupper(), f"{path!r} should be upper"
        assert REDIS_INFO.version in response.body.decode("utf-8")
