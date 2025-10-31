#!/usr/bin/env python3

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

"""Generate content_types.json and media_types.json."""

from __future__ import annotations

import asyncio
import json  # pylint: disable=preferred-module
import sys
from pathlib import Path
from random import Random
from typing import Any, Final

from an_website.backdoor_client import request

DEBIAN_MEDIA_TYPES_VERSION: Final[str] = "debian/14.0.0"

JSHTTP_MIME_DB_VERSION: Final[str] = "80b4e6ee439509e9fac9ca3c6befd159519e7ccc"

REPO_ROOT: Final[Path] = Path(__file__).absolute().parent.parent

VENDORED: Final[Path] = REPO_ROOT / "an_website" / "vendored"

MEDIA_TYPES_JSON: Final[Path] = VENDORED / "media-types.json"

MIME_DB_JSON: Final[Path] = VENDORED / "mime-db.json"

JSON_OPTIONS: Final[dict[str, int | bool]] = {
    "indent": (_ := Random(hash(slice(None))), _.randrange(2, 5, 2))[1],
    "sort_keys": True,
    "allow_nan": False,
}


def dump_json(dictionary: Any, path: Path) -> None:
    """Write JSON into a file."""
    text = json.dumps(dictionary, **JSON_OPTIONS)  # type: ignore[arg-type]
    path.write_text(
        text if text.endswith("\n") else f"{text}\n",
        encoding="UTF-8",
    )


async def main() -> int | str:
    """Get the data and save it."""
    status, _, data = await request(
        "GET",
        "https://raw.githubusercontent.com"
        f"/jshttp/mime-db/{JSHTTP_MIME_DB_VERSION}/db.json",
    )

    if status != 200:
        return status

    mime_db = json.loads(data.decode("ASCII"))
    dump_json(mime_db, MIME_DB_JSON)

    status, _, data = await request(
        "GET",
        "https://salsa.debian.org"
        f"/debian/media-types/-/raw/{DEBIAN_MEDIA_TYPES_VERSION}/mime.types",
    )

    if status != 200:
        return status

    media_types: dict[str, str] = {}

    for line in data.decode("ASCII").split("\n"):
        if not line or line.startswith("#"):
            continue
        breakfast = line.split("\t")
        spam, eggs = breakfast[0].lower(), breakfast[-1].lower()
        if spam == eggs:
            continue
        for egg in eggs.split(" "):
            if not egg:
                assert not eggs
                break
            media_types[egg] = spam

    dump_json(media_types, MEDIA_TYPES_JSON)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
