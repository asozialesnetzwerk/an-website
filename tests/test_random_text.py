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

"""The tests for the random text API."""

from __future__ import annotations

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_response,
    fetch,
)

PATH = "/api/zufaelliger-text"


async def test_random_text_api(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the random text API."""
    assert_valid_response(await fetch(PATH), "text/plain", {200})

    assert_valid_html_response(
        await fetch(PATH + "?words=10", headers={"Accept": "text/html"}),
        codes={200},
        assert_canonical=False,
    )


async def test_random_text_seed(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the random text API."""
    seeded_path = f"{PATH}?seed=xyz"

    assert (await fetch(seeded_path)).body == (await fetch(seeded_path)).body

    assert (await fetch(seeded_path, headers={"Accept": "text/html"})).body == (
        await fetch(seeded_path, headers={"Accept": "text/html"})
    ).body
