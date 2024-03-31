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
from collections.abc import Awaitable, Mapping
from functools import cache
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Final, cast

import defity
import orjson as json
import tornado.web
from blake3 import blake3
from openmoji_dist import VERSION as OPENMOJI_VERSION
from openmoji_dist import get_openmoji_data

from .. import DIR as ROOT_DIR
from .. import STATIC_DIR
from .utils import Handler

LOGGER: Final = logging.getLogger(__name__)


def hash_file(path: str | Path) -> str:
    """Hash a file with BLAKE3."""
    with open(path, "rb") as file:
        return blake3(file.read()).hexdigest(8)


def create_file_hashes_dict() -> dict[str, str]:
    """Create a dict of file hashes."""
    file_hashes_dict = {
        str(path)[len(ROOT_DIR) :].replace(os.path.sep, "/"): hash_file(path)
        for path in Path(STATIC_DIR).rglob("*")
        if path.is_file()
    }
    file_hashes_dict["/favicon.png"] = file_hashes_dict["/static/favicon.png"]
    file_hashes_dict["/favicon.jxl"] = file_hashes_dict["/static/favicon.jxl"]
    file_hashes_dict["/humans.txt"] = file_hashes_dict["/static/humans.txt"]
    return file_hashes_dict


FILE_HASHES_DICT: Final[Mapping[str, str]] = create_file_hashes_dict()

CONTENT_TYPES: Final[Mapping[str, str]] = json.loads(
    Path(ROOT_DIR, "vendored", "media-types.json").read_bytes()
)


def get_handlers() -> list[Handler]:
    """Return a list of handlers for static files."""
    # pylint: disable=import-outside-toplevel, cyclic-import
    from .static_file_from_traversable import TraversableStaticFileHandler

    handlers: list[Handler] = [
        (
            "/static/openmoji/(.*)",
            TraversableStaticFileHandler,
            {"root": get_openmoji_data()},
        ),
        (
            r"(?:/static)?/(\.env|favicon\.(?:png|jxl)|humans\.txt|robots\.txt)",
            StaticFileHandler,
            {"path": STATIC_DIR},
        ),
        (
            "/favicon.ico",
            tornado.web.RedirectHandler,
            {"url": fix_static_path("favicon.png")},
        ),
    ]
    debug_style_dir = Path(ROOT_DIR).absolute().parent / "style"
    if sys.flags.dev_mode and debug_style_dir.exists():
        # add handlers for the unminified CSS files
        handlers.append(
            (
                r"/static/css/(.+\.css)",
                StaticFileHandler,
                {"path": str(debug_style_dir)},
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
    if path.startswith("/static/openmoji/"):
        return f"{path}?v={OPENMOJI_VERSION}"
    path = path.lower()
    if path.startswith("/static/js/utils/"):  # TODO: improve this
        return path
    if path in FILE_HASHES_DICT:
        hash_ = FILE_HASHES_DICT[path]
        return f"{path}?v={hash_}"
    LOGGER.warning("%s not in FILE_HASHES_DICT", path)
    return path


def content_type_from_path(url_path: str, file: Traversable) -> str | None:
    """Extract the Content-Type from a path."""
    content_type: str | None = CONTENT_TYPES.get(Path(url_path).suffix[1:])
    if not content_type:
        with file.open("rb") as io:
            content_type = defity.from_file(io)
    if content_type and content_type.startswith("text/"):
        content_type += "; charset=UTF-8"
    return content_type


class StaticFileHandler(tornado.web.StaticFileHandler):
    """A StaticFileHandler with smart Content-Type."""

    content_type: None | str
    keep_case: bool

    def data_received(self, chunk: bytes) -> None | Awaitable[None]:
        """Do nothing."""

    async def get(self, path: str, include_body: bool = True) -> None:
        """Handle GET requests."""
        if self.keep_case:
            return await super().get(path, include_body=include_body)
        return await super().get(
            path.lower(),
            include_body=include_body,
        )

    async def head(self, path: str) -> None:
        # pylint: disable=invalid-overridden-method
        """Handle HEAD requests."""
        return await self.get(path)

    def initialize(
        self,
        path: str,
        default_filename: None | str = None,
        content_type: None | str = None,
        keep_case: bool = False,
    ) -> None:
        """Initialize the handler."""
        super().initialize(path=path, default_filename=default_filename)
        self.content_type = content_type
        self.keep_case = keep_case

    def set_extra_headers(self, _: str) -> None:
        """Reset the Content-Type header if we know it better."""
        if not self.content_type:
            self.content_type = content_type_from_path(
                self.path, Path(cast(str, self.absolute_path))
            )
        if self.content_type:
            self.set_header("Content-Type", self.content_type)


class CachedStaticFileHandler(StaticFileHandler):
    """A static file handler that sets a smarter Cache-Control header."""

    def compute_etag(self) -> None | str:
        """Don't compute ETag, because it isn't necessary."""
        return None

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
        if not sys.flags.dev_mode and "v" in self.request.arguments:
            self.set_header(  # never changes
                "Cache-Control",
                f"public, immutable, max-age={self.CACHE_MAX_AGE}",
            )
