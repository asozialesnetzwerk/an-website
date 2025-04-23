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

"""The tests for the output of /scripts/compres_static_files.py."""

from __future__ import annotations

import contextlib
import gzip

from an_website import DIR as ROOT_DIR
from an_website.utils.fix_static_path_impl import recurse_directory

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    fetch,
)

STATIC_DIR = ROOT_DIR / "static"


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
            response = await fetch(
                f"/static/{file}", headers={"Accept-Encoding": encoding}
            )
            body = response.body
            assert response.code == 200
            assert response.headers["Content-Length"] == str(len(body))
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
                with contextlib.suppress(ModuleNotFoundError):
                    import zstd
                    decompressed_body = zstd.decompress(body)
                    assert uncompressed_body == decompressed_body
                with contextlib.suppress(ModuleNotFoundError):
                    import zstandard
                    decompressed_body = zstandard.decompress(body)
            else:
                raise AssertionError(f"Unknown encoding {encoding}")

            assert decompressed_body
            assert uncompressed_body == decompressed_body

    assert file_count >= gzip_count > 0
    assert file_count >= zstd_count > 0
