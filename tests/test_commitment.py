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

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import emoji
from time_machine import travel

from an_website.commitment import commitment

from . import (  # noqa: F401  # pylint: disable=unused-import
    DIR,
    FetchCallable,
    app,
    assert_valid_json_response,
    assert_valid_response,
    assert_valid_yaml_response,
    fetch,
)


@contextmanager
def patch_commits_data() -> Iterator[object]:
    """Patch the commits data."""
    commits = commitment.COMMITS
    file = Path(DIR) / "commitment.txt"
    data = commitment.parse_commits_txt(file.read_text())
    if commits is not None:
        assert set(commits) & set(data)
    commitment.COMMITS = data

    try:
        yield None
    finally:
        commitment.COMMITS = commits


def test_parsing() -> None:
    """Test parsing the commitment data."""
    with patch_commits_data():
        assert (data := commitment.COMMITS)

        assert len(list(data)) == 2

        assert data["50821273052022fbc283e310e09168dc65fb3cce"] == (
            datetime(2022, 8, 29, 19, 56, 6, tzinfo=UTC),
            "💬 fix kangaroo comic of today",
        )

        assert data["7335914237808031fa15f32a854ba1e6b1544420"] == (
            datetime(2021, 7, 21, 22, 29, 26, tzinfo=UTC),
            "no_js → no_3rd_party",
        )


async def test_text_api(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the commitment API."""
    assert commitment.COMMITS, "Please create commits.txt"
    for _ in range(100):  # do it many times to make sure it's not flaky
        response = assert_valid_response(
            await fetch("/api/commitment", headers={"Accept": "*/*"}),
            "text/plain;charset=utf-8",
        )

        assert response.body.decode("UTF-8").endswith("\n")

        response = assert_valid_response(
            await fetch(
                "/api/commitment?require_emoji=sure", headers={"Accept": "*/*"}
            ),
            "text/plain;charset=utf-8",
        )

        assert response.body.decode("UTF-8").endswith("\n")
        assert emoji.emoji_count(response.body.decode("UTF-8"))


async def test_text_api_patched(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the commitment API."""
    with patch_commits_data():
        response = assert_valid_response(
            await fetch("/api/commitment", headers={"Accept": "*/*"}),
            "text/plain;charset=utf-8",
        )

        assert response.body.decode("UTF-8").endswith("\n")
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

        assert response.body.decode("UTF-8").endswith("\n")
        assert (
            response.body.decode("UTF-8") == "💬 fix kangaroo comic of today\n"
        )


async def test_json_api(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the JSON API."""
    with patch_commits_data():
        for query in (
            "hash=5&require_emoji=sure",
            "hash=50821",
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


@travel(datetime(2021, 7, 21, 22, 29, 26, tzinfo=UTC), tick=False)
async def test_yaml_api(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the YAML API."""
    with patch_commits_data():
        for query in (
            "hash=7",
            "hash=733591",
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
            assert len(response) == 3
            assert response == {
                "commit_message": "no_js → no_3rd_party",
                "date": datetime.now(UTC),
                "hash": "7335914237808031fa15f32a854ba1e6b1544420",
            }


async def test_api_404(fetch: FetchCallable) -> None:  # noqa: F811
    """Test getting non-existent hashes."""
    with patch_commits_data():
        for query in (
            "hash=7&require_emoji=sure",
            "hash=7335914237808031fa15f32a854ba1e6b154442&require_emoji=sure",
            "hash=9168045768942198",
            "hash=9168045768942198e1fbe5e3f00e133b5377a5fa",
            "hash=9168045768942198e1fbe5e3f00e133b5377a5fa6",  # too long
            "hash=x",
            "hash=xxxxxxxxxxxxxxxx",
            "hash=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "hash=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  # too long
        ):
            response = assert_valid_response(
                await fetch(
                    f"/api/commitment?{query}", headers={"Accept": "*/*"}
                ),
                "text/plain;charset=utf-8",
                codes={404},
            )
            assert response.body == b"404 Not Found\n"
