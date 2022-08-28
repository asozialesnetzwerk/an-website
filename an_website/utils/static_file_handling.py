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
import os
import sys
from collections.abc import Awaitable
from functools import cache
from pathlib import Path
from typing import Any, cast

import defity
import orjson as json
import tornado.web
from blake3 import blake3  # type: ignore[import]

from .. import DIR as ROOT_DIR
from .. import STATIC_DIR
from .utils import Handler

logger = logging.getLogger(__name__)


def hash_file(path: str | Path) -> str:
    """Hash a file with BLAKE3."""
    with open(path, "rb") as file:
        return cast(str, blake3(file.read()).hexdigest(8))


def create_file_hashes_dict() -> dict[str, str]:
    """Create a dict of file hashes."""
    file_hashes_dict = {
        str(path).removeprefix(ROOT_DIR): hash_file(path)
        for path in Path(STATIC_DIR).rglob("*")
        if path.is_file() and "img/openmoji-svg-" not in str(path)
    }
    file_hashes_dict["/favicon.png"] = file_hashes_dict["/static/favicon.png"]
    file_hashes_dict["/humans.txt"] = file_hashes_dict["/static/humans.txt"]
    return file_hashes_dict


FILE_HASHES_DICT = create_file_hashes_dict()

MEDIA_TYPES: dict[str, str] = json.loads(
    Path(os.path.join(ROOT_DIR, "media_types.json")).read_bytes()
)


def get_handlers() -> list[Handler]:
    """Return a list of handlers for static files."""
    handlers: list[Handler] = [
        (
            r"/(?:static/)?(\.env|favicon\.png|humans\.txt|robots\.txt)",
            StaticFileHandler,
            {"path": STATIC_DIR},
        ),
        (
            r"/favicon\.ico",
            tornado.web.RedirectHandler,
            {"url": fix_static_path("/favicon.png")},
        ),
    ]
    if sys.flags.dev_mode:
        # add handlers for the unminified CSS files
        handlers.append(
            (
                r"/static/css/(.+\.css)",
                StaticFileHandler,
                {"path": os.path.join(os.path.dirname(ROOT_DIR), "style")},
            )
        )
    handlers.append(
        (r"/static/(.*)", CachedStaticFileHandler, {"path": STATIC_DIR})
    )
    return handlers


@cache
def fix_static_path(path: str) -> str:
    """Fix the path for static files."""
    if not path.startswith("/"):
        path = f"/static/{path}"
    if "?" in path:
        path = path.split("?")[0]
    if path.startswith("/static/img/openmoji-svg-"):
        return path
    if path in FILE_HASHES_DICT:
        hash_ = FILE_HASHES_DICT[path]
        return f"{path}?v={hash_}"
    logger.warning("%s not in FILE_HASHES_DICT", path)
    return path


class StaticFileHandler(tornado.web.StaticFileHandler):
    """A StaticFileHandler with smart Content-Type."""

    content_type: None | str

    def data_received(  # noqa: D102
        self, chunk: bytes
    ) -> None | Awaitable[None]:
        pass

    def head(self, path: str) -> Awaitable[None]:
        """Handle HEAD requests."""
        return self.get(path)

    def initialize(
        self,
        path: str,
        default_filename: None | str = None,
        content_type: None | str = None,
    ) -> None:
        """Initialize the handler."""
        super().initialize(path=path, default_filename=default_filename)
        self.content_type = content_type

    def set_extra_headers(self, _: str) -> None:
        """Reset the Content-Type header if we know it better."""
        if self.content_type:
            self.set_header("Content-Type", self.content_type)

    def validate_absolute_path(
        self, root: str, absolute_path: str
    ) -> None | str:
        """Validate the path and detect the content type."""
        if (
            path := super().validate_absolute_path(root, absolute_path)
        ) and not self.content_type:
            self.content_type = MEDIA_TYPES.get(Path(path).suffix[1:])
            if not self.content_type:
                self.content_type = defity.from_file(path)
        return path


class CachedStaticFileHandler(StaticFileHandler):
    """A static file handler that sets a smarter Cache-Control header."""

    def compute_etag(self) -> None | str:
        """Don't compute ETag, because it isn't necessary."""
        return None

    def data_received(  # noqa: D102
        self, chunk: bytes
    ) -> None | Awaitable[None]:
        pass

    @classmethod
    def make_static_path(
        cls, settings: dict[str, Any], path: str, include_version: bool = True
    ) -> str:
        """Make a static path for the given path."""
        # pylint: disable=unused-argument
        return fix_static_path(path)

    def set_headers(self) -> None:
        """Set the default headers for this handler."""
        super().set_headers()
        if not sys.flags.dev_mode and (
            "v" in self.request.arguments
            # guaranteed uniqueness is done via the 14.0 in the folder name
            or self.path.startswith("/static/img/openmoji-svg-")
        ):
            self.set_header(  # never changes
                "Cache-Control",
                f"public, immutable, min-fresh={60 * 60 * 24 * 365 * 10}",
            )
