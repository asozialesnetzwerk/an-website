#!/usr/bin/env python3

"""Run zipapps with customized compression."""

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

import os
import zipfile

import zopfli
from zipapps.__main__ import main  # type: ignore[import-untyped]

DO_NOT_COMPRESS = (
    "an_website/static/",
    "an_website/soundboard/files/",
    "an_website/vendored/apm-rum/",
    "openmoji_dist/openmoji/",
)


class ZipFile(zopfli.ZipFile):
    """ZipFile with custom compression logic."""

    def write(
        self,
        filename: str | os.PathLike[str],
        arcname: str | os.PathLike[str] | None = None,
        compress_type: int | None = None,
        compresslevel: int | None = None,
        **kwargs: object,
    ) -> None:
        """Write with custom compression logic."""
        # assert current calling behaviour of zipapp.py
        assert self.compression == zipfile.ZIP_STORED
        assert not kwargs
        assert compress_type is None
        assert compresslevel is None
        assert arcname is not None
        assert isinstance(arcname, str)

        if arcname.startswith(DO_NOT_COMPRESS):
            return super().write(filename, arcname)

        if arcname.endswith(".py"):
            return super().write(
                filename,
                arcname,
                compress_type=zipfile.ZIP_DEFLATED,
            )

        return super().write(
            filename,
            arcname,
            compress_type=zipfile.ZIP_ZSTANDARD,
            compresslevel=22,
        )


if __name__ == "__main__":
    zipfile.ZipFile = ZipFile  # type: ignore[assignment, misc]

    main()
