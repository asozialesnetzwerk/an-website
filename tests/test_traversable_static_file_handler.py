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

import gzip

import zstandard

from an_website import DIR as ROOT_DIR
from an_website.utils.fix_static_path_impl import recurse_directory

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_response,
    fetch,
)

STATIC_DIR = ROOT_DIR / "static"
CACHE_CONTROL = f"public, immutable, max-age={86400 * 365 * 10}"


async def test_well_known(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the /.well-known handler."""
    assert_valid_response(
        await fetch("/.well-known/test-file"),
        content_type="text/plain;charset=utf-8",
        codes={404},
        headers={"Access-Control-Allow-Origin": "*"},
    )


async def test_openmoji(fetch: FetchCallable) -> None:  # noqa: F811
    """Test requesting an OpenMoji svg."""
    response = assert_valid_response(
        await fetch("/static/openmoji/svg/1F973.svg?v=15.0.0"),
        content_type="image/svg+xml",
        codes={200},
    )
    assert response.headers["Cache-Control"] == CACHE_CONTROL
    size = len(response.body)

    for encoding in ("gzip", "zstd"):
        compressed_response = await fetch(
            "/static/openmoji/svg/1F973.svg?v=15.0.0",
            headers={"Accept-Encoding": encoding},
        )
        assert size > (size_compre := len(compressed_response.body))
        assert compressed_response.headers["Content-Encoding"] == encoding
        assert int(compressed_response.headers["Content-Length"]) == size_compre
        if encoding == "gzip":
            assert response.body == gzip.decompress(compressed_response.body)
        if encoding == "zstd":
            assert response.body == zstandard.decompress(
                compressed_response.body
            )

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


async def test_static_file_compression(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test fetching static files."""
    file_count, gzip_count, zstd_count = 0, 0, 0

    for file in recurse_directory(
        STATIC_DIR,
        filter=lambda p: p.is_file() and not p.name.endswith((".zst", ".gz")),
    ):
        gzip_file = (STATIC_DIR / f"{file}.gz").is_file()
        zstd_file = (STATIC_DIR / f"{file}.zst").is_file()

        file_count += 1
        gzip_count += gzip_file
        zstd_count += zstd_file

        uncompressed_body = b""

        for encoding in ("identity", "gzip", "zstd"):
            headers = {"Accept-Encoding": encoding}
            response = await fetch(f"/static/{file}", headers=headers)
            body = response.body
            assert response.code == 200
            assert response.headers["Content-Length"] == str(len(body))

            head_response = await fetch(
                f"/static/{file}", headers=headers, method="HEAD"
            )
            assert head_response.code == 200
            assert head_response.headers["Content-Length"] == str(len(body))

            headers = dict(response.headers)
            head_headers = dict(head_response.headers)
            del head_headers["Date"], headers["Date"]
            assert head_headers == headers, f"{head_headers} != {headers}"

            if encoding == "identity":
                assert "Content-Encoding" not in response.headers
                uncompressed_body = body
                continue
            if "Content-Encoding" not in response.headers:
                if encoding == "gzip":
                    assert not gzip_file
                elif encoding == "zstd":
                    assert not zstd_file
                else:
                    raise AssertionError(f"Unknown encoding {encoding}")
                continue

            assert response.headers.get("Content-Encoding") == encoding

            body = response.body
            assert len(body) < len(uncompressed_body)

            decompressed_body = b""
            if encoding == "gzip":
                assert gzip_file
                decompressed_body = gzip.decompress(body)
            elif encoding == "zstd":
                assert zstd_file
                decompressed_body = zstandard.decompress(body)
            else:
                raise AssertionError(f"Unknown encoding {encoding}")

            assert decompressed_body
            assert uncompressed_body == decompressed_body

    assert file_count >= gzip_count > 0
    assert file_count >= zstd_count > 0


async def test_invalid_paths(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test various different invalid paths."""
    response = await fetch("/static/humans.txt/")
    assert response.code == 307
    assert response.headers["location"].endswith("/static/humans.txt")

    response = await fetch("/static//humans.txt")
    assert response.code == 404

    response = await fetch("/static/INVALID_FILE")
    assert response.code == 404

    response = await fetch("/static/HUMANS.TXT")
    assert response.code == 307
    assert response.headers["location"].endswith("/static/humans.txt")


async def test_invalid_range(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test invalid range requests."""
    for encoding in ("identity", "gzip", "zstd"):
        headers = {"Accept-Encoding": encoding}

        response = await fetch("/static/robots.txt", headers=headers)
        size = len(response.body)

        response = await fetch(
            "/static/robots.txt", headers={**headers, "Range": f"bytes={size}"}
        )
        assert response.code == 416
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["Content-Range"] == f"bytes */{size}"

        response = await fetch(
            "/static/robots.txt",
            headers={**headers, "Range": f"bytes={size * 2 + 100}"},
        )
        assert response.code == 416
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["Content-Range"] == f"bytes */{size}"

        response = await fetch(
            "/static/robots.txt", headers={**headers, "Range": "bytes=-0"}
        )
        assert response.code == 416
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["Content-Range"] == f"bytes */{size}"
