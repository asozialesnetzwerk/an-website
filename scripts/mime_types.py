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
from typing import Any, Final, TypedDict

from an_website.backdoor.client import request


class MediaType(TypedDict, total=False):  # noqa: D101
    # pylint: disable=missing-class-docstring
    charset: str
    compressible: bool
    extensions: list[str]
    source: str


MediaTypes = dict[str, MediaType]

VERSION: Final[str] = "a76e5a824c228e2e58363c9404e42a54ee1d142f"

URL: Final[
    str
] = f"https://raw.githubusercontent.com/jshttp/mime-db/{VERSION}/db.json"

REPO_ROOT: Final[Path] = Path(__file__).absolute().parent.parent

CONTENT_TYPES_JSON: Final[Path] = (
    REPO_ROOT / "an_website" / "content_types.json"
)

MEDIA_TYPES_JSON: Final[Path] = REPO_ROOT / "an_website" / "media_types.json"

PREFERENCE: Final[tuple[str | None, ...]] = ("nginx", "apache", None, "iana")

HEADERS: Final[dict[str, str]] = {"Accept": "application/json"}

JSON_OPTIONS: Final[dict[str, int | bool]] = {
    "indent": 2,
    "sort_keys": True,
    "allow_nan": False,
}

ADDITIONAL_MEDIA_TYPES: Final[MediaTypes] = {
    "image/jxl": {
        "extensions": ["jxl"],
    },
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
    status, _, data = await request("GET", URL, HEADERS)

    if status != 200:
        return 1

    media_types: MediaTypes = json.loads(data.decode("UTF-8"))
    media_types.update(ADDITIONAL_MEDIA_TYPES)
    dump_json(media_types, MEDIA_TYPES_JSON)

    content_types: list[tuple[int, int, int, str, str]] = []

    for mime_type, mapping in media_types.items():
        preference: int = PREFERENCE.index(mapping.get("source"))

        if "charset" in mapping:
            # pylint: disable=redefined-loop-name
            mime_type += f"; charset={mapping['charset']}"
        elif mime_type.startswith("text/"):
            # pylint: disable=redefined-loop-name
            mime_type += "; charset=UTF-8"

        extensions = mapping.get("extensions", [])

        for ext in extensions:
            content_types.append(
                (
                    int("vnd." not in mime_type and "/x-" not in mime_type)
                    if mime_type != "application/octet-stream"
                    else -1,
                    preference,
                    -len(extensions),
                    ext,
                    mime_type,
                )
            )

    content_types_dict: dict[str, str] = {
        ext: mime_type for _, _, _, ext, mime_type in sorted(content_types)
    }
    dump_json(content_types_dict, CONTENT_TYPES_JSON)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
