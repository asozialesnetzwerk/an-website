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

"""The tests for commitment."""

from __future__ import annotations

from datetime import datetime
from os.path import join

from an_website.commitment.commitment import get_commit_data

from . import (
    DIR,
    FetchCallable,
    app,
    assert_valid_json_response,
    assert_valid_response,
    assert_valid_yaml_response,
    fetch,
)

assert fetch and app


async def test_parsing() -> None:
    """Make request to the backdoor and parse the response."""
    data = await get_commit_data(join(DIR, "commits.txt"))

    assert len(data) == 2

    assert data["50821273052022fbc283e310e09168dc65fb3cce"] == (
        datetime(2022, 8, 29, 19, 56, 6),
        "💬 fix kangaroo comic of today",
    )
    assert data["7335914237808031fa15f32a854ba1e6b1544420"] == (
        datetime(2021, 7, 21, 22, 29, 26),
        "no_js → no_3rd_party",
    )


async def test_text_api(fetch: FetchCallable) -> None:
    """Test the commitment API."""
    response = assert_valid_response(
        await fetch("/api/commitment", headers={"Accept": "*/*"}),
        "text/plain;charset=utf-8",
    )
    assert response.body.decode("UTF-8") in {
        "💬 fix kangaroo comic of today\n",
        "no_js → no_3rd_party\n",
    }

    response = assert_valid_response(
        await fetch(
            "/api/commitment?require_emoji=sure", headers={"Accept": "*/*"}
        ),
        "text/plain;charset=utf-8",
    )
    assert response.body.decode("UTF-8") == "💬 fix kangaroo comic of today\n"


async def test_json_api(fetch: FetchCallable) -> None:
    """Test the json API."""
    for query in (
        "require_emoji=sure",
        "hash=5",
        "hash=50821273052022",
        "hash=50821273052022fbc283e310e09168dc65fb3cce",
    ):
        response = assert_valid_json_response(
            await fetch(
                f"/api/commitment?{query}",
                headers={"Accept": "application/json"},
            ),
        )
        assert response["permalink"].endswith(
            "/api/commitment?hash=50821273052022fbc283e310e09168dc65fb3cce"
        )
        del response["permalink"]
        assert response == {
            "commit_message": "💬 fix kangaroo comic of today",
            "hash": "50821273052022fbc283e310e09168dc65fb3cce",
            "date": "2022-08-29T19:56:06Z",
        }


async def test_yaml_api(fetch: FetchCallable) -> None:
    """Test the yaml API."""
    for query in (
        "hash=7",
        "hash=7335914237808031",
        "hash=7335914237808031fa15f32a854ba1e6b1544420",
    ):
        response = assert_valid_yaml_response(
            await fetch(
                f"/api/commitment?{query}",
                headers={"Accept": "application/yaml"},
            ),
        )
        assert response["permalink"].endswith(
            "/api/commitment?hash=7335914237808031fa15f32a854ba1e6b1544420"
        )
        del response["permalink"]
        assert response == {
            "commit_message": "no_js → no_3rd_party",
            "hash": "7335914237808031fa15f32a854ba1e6b1544420",
            "date": datetime(2021, 7, 21, 22, 29, 26),  # yaml > json
        }
