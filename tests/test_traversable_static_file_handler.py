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

"""The tests for the TraversableStaticFileHandler."""

from __future__ import annotations

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_response,
    fetch,
)

CACHE_CONTROL = f"public, immutable, max-age={86400 * 365 * 10}"


async def test_openmoji(fetch: FetchCallable) -> None:  # noqa: F811
    """Test requesting an OpenMoji svg."""
    response = assert_valid_response(
        await fetch("/static/openmoji/svg/1F973.svg?v=15.0.0"),
        content_type="image/svg+xml",
        codes={200},
    )
    assert response.headers["Cache-Control"] == CACHE_CONTROL
    size = len(response.body)

    part_response = assert_valid_response(
        await fetch(
            "/static/openmoji/svg/1F973.svg?v=15.0.0",
            headers={"Range": "bytes=17-41"},
        ),
        content_type="image/svg+xml",
        codes={206},
        needs_to_end_with_line_feed=False,
    )
    assert part_response.headers["Cache-Control"] == CACHE_CONTROL
    assert part_response.headers["Content-Range"] == f"bytes 17-41/{size}"
    assert int(part_response.headers["Content-Length"]) == 25

    part_response = assert_valid_response(
        await fetch(
            "/static/openmoji/svg/1F973.svg?v=15.0.0",
            headers={"Range": "bytes=0-3"},
        ),
        content_type="image/svg+xml",
        codes={206},
        needs_to_end_with_line_feed=False,
    )
    assert part_response.headers["Cache-Control"] == CACHE_CONTROL
    assert part_response.headers["Content-Range"] == f"bytes 0-3/{size}"
    assert int(part_response.headers["Content-Length"]) == 4
    assert part_response.body == b"<svg"

    part_response = assert_valid_response(
        await fetch(
            "/static/openmoji/svg/1F973.svg?v=15.0.0",
            headers={"Range": f"bytes={size - 7}-{size}"},
        ),
        content_type="image/svg+xml",
        codes={206},
    )
    assert part_response.headers["Cache-Control"] == CACHE_CONTROL
    assert (
        part_response.headers["Content-Range"]
        == f"bytes {size - 7}-{size - 1}/{size}"
    )
    assert int(part_response.headers["Content-Length"]) == 7
    assert part_response.body == b"</svg>\n"

    part_response = assert_valid_response(
        await fetch(
            "/static/openmoji/svg/1F973.svg?v=15.0.0",
            headers={"Range": "bytes=-7"},
        ),
        content_type="image/svg+xml",
        codes={206},
    )
    assert part_response.headers["Cache-Control"] == CACHE_CONTROL
    assert (
        part_response.headers["Content-Range"]
        == f"bytes {size - 7}-{size - 1}/{size}"
    )
    assert int(part_response.headers["Content-Length"]) == 7
    assert part_response.body == b"</svg>\n"
