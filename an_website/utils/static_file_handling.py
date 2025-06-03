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

"""Useful stuff for handling static files."""

from __future__ import annotations

import logging
import sys
from collections.abc import Mapping
from functools import cache
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Final

import defity
import orjson as json
import tornado.web
from openmoji_dist import get_openmoji_data

from .. import DIR as ROOT_DIR, STATIC_DIR
from .fix_static_path_impl import (
    create_file_hashes_dict,
    fix_static_path_impl,
)
from .utils import Handler

LOGGER: Final = logging.getLogger(__name__)

FILE_HASHES_DICT: Final[Mapping[str, str]] = create_file_hashes_dict()

CONTENT_TYPES: Final[Mapping[str, str]] = json.loads(
    (ROOT_DIR / "vendored" / "media-types.json").read_bytes()
)


def get_handlers() -> list[Handler]:
    """Return a list of handlers for static files."""
    # pylint: disable=import-outside-toplevel, cyclic-import
    from .static_file_from_traversable import TraversableStaticFileHandler

    handlers: list[Handler] = [
        (
            "/static/openmoji/(.*)",
            TraversableStaticFileHandler,
            {"root": get_openmoji_data(), "hashes": {}},
        ),
        (
            r"(?:/static)?/(\.env|favicon\.(?:png|jxl)|humans\.txt|robots\.txt)",
            TraversableStaticFileHandler,
            {"root": STATIC_DIR, "hashes": FILE_HASHES_DICT},
        ),
        (
            "/favicon.ico",
            tornado.web.RedirectHandler,
            {"url": fix_static_path("favicon.png")},
        ),
        (
            r"/static/(img/netcup-oekostrom2\..*)",
            TraversableStaticFileHandler,
            {
                "root": STATIC_DIR,
                "hashes": FILE_HASHES_DICT,
                "headers": (("X-Robots-Tag", "noindex, nofollow"),),
            },
        ),
    ]
    debug_style_dir = (
        ROOT_DIR.absolute().parent / "style"
        if isinstance(ROOT_DIR, Path)
        else None
    )
    if sys.flags.dev_mode and debug_style_dir and debug_style_dir.exists():
        # add handlers for the unminified CSS files
        handlers.append(
            (
                r"/static/css/(.+\.css)",
                TraversableStaticFileHandler,
                {"root": debug_style_dir, "hashes": {}},
            )
        )

    handlers.append(
        (
            r"/static/(.*)",
            TraversableStaticFileHandler,
            {"root": STATIC_DIR, "hashes": FILE_HASHES_DICT},
        )
    )
    return handlers


@cache
def fix_static_path(path: str) -> str:
    """Fix the path for static files."""
    return fix_static_path_impl(path, FILE_HASHES_DICT)


def content_type_from_path(url_path: str, file: Traversable) -> str | None:
    """Extract the Content-Type from a path."""
    content_type: str | None = CONTENT_TYPES.get(Path(url_path).suffix[1:])
    if not content_type:
        with file.open("rb") as io:
            content_type = defity.from_file(io)
    if content_type and content_type.startswith("text/"):
        content_type += "; charset=UTF-8"
    return content_type
