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

import tornado.web
from blake3 import blake3  # type: ignore
from tornado.web import GZipContentEncoding, OutputTransform

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
    return {
        str(path).removeprefix(ROOT_DIR): hash_file(path)
        for path in Path(STATIC_DIR).rglob("*")
        if path.is_file()
    }


FILE_HASHES_DICT: dict[str, str] = create_file_hashes_dict()


def get_handlers() -> list[Handler]:
    """Return a list of handlers for static files."""
    handlers: list[Handler] = [
        (
            r"/(?:static/)?(robots\.txt|\.env)",
            StaticFileHandler,
            {"path": STATIC_DIR, "content_type": "text/plain;charset=ascii"},
        ),
        (
            r"/(?:static/)?(humans\.txt)",
            StaticFileHandler,
            {"path": STATIC_DIR, "content_type": "text/plain;charset=utf-8"},
        ),
        (
            r"/(?:static/)?(favicon\.ico)",
            CachedStaticFileHandler,
            {"path": STATIC_DIR, "content_type": "image/x-icon"},
        ),
    ]
    if sys.flags.dev_mode:
        # add handlers for the not minified CSS files
        handlers.append(
            (
                r"/static/style/(.+\.css)",
                StaticFileHandler,
                {"path": os.path.join(os.path.dirname(ROOT_DIR), "style")},
            )
        )
        # add handlers for the not minified JS files
        for folder, _, files in os.walk(
            ROOT_DIR,
            topdown=True,
            onerror=None,
            followlinks=False,
        ):
            if folder != os.path.join(STATIC_DIR, "js"):
                handlers.extend(
                    (
                        f"/static/js/({file})",
                        StaticFileHandler,
                        {"path": folder},
                    )
                    for file in files
                    if file.endswith(".js")
                )

    # static files in "/static/"; add it here (after the CSS & JS handlers)
    handlers.append(
        (r"/static/(.*)", CachedStaticFileHandler, {"path": STATIC_DIR})
    )
    return handlers


@cache
def fix_static_url(url: str) -> str:
    """Fix the URL for static files."""
    if not url.startswith("/static/"):
        url = f"/static/{url}"
    if "?" in url:
        url = url.split("?")[0]
    if url in FILE_HASHES_DICT:
        hash_ = FILE_HASHES_DICT[url]
        if url == "/static/favicon.ico":
            return f"/favicon.ico?v={hash_}"
        return f"{url}?v={hash_}"
    logger.warning("%s not in FILE_HASHES_DICT", url)
    return url


GZipContentEncoding.MIN_LENGTH = 666  # from my tests this seems to be better 👿


class StaticFileHandler(tornado.web.StaticFileHandler):
    """A StaticFileHandler with customizable Content-Type header and gzip."""

    content_type: None | str
    transforms: list[OutputTransform]

    def data_received(self, chunk: bytes) -> None | Awaitable[None]:
        pass

    def initialize(
        self,
        path: str,
        default_filename: None | str = None,
        content_type: None | str = None,
    ) -> None:
        """Initialize the handler."""
        super().initialize(path=path, default_filename=default_filename)
        self.content_type = content_type
        self.transforms = [GZipContentEncoding(self.request)]

    def head(self, path: str) -> Awaitable[None]:
        """Handle head requests correct but slow."""
        return self.get(path)

    def set_extra_headers(self, _: str) -> None:
        """Reset the Content-Type header if we know it better."""
        if self.content_type:
            self.set_header("Content-Type", self.content_type)

    @property  # type: ignore
    def _transforms(self) -> list["OutputTransform"]:  # type: ignore
        """Enable gzip encoding for this handler."""
        return self.transforms

    @_transforms.setter
    def _transforms(
        # pylint: disable=no-self-use
        self,
        transforms: list["OutputTransform"],
    ) -> None:
        """Prevent the transforms from being overwritten."""
        assert not transforms


class CachedStaticFileHandler(StaticFileHandler):
    """A static file handler that sets a smarter Cache-Control header."""

    def data_received(self, chunk: bytes) -> None | Awaitable[None]:
        pass

    @classmethod
    def make_static_url(
        cls, settings: dict[str, Any], path: str, include_version: bool = True
    ) -> str:
        """Make a static url for the given path."""
        return fix_static_url(path)

    def set_headers(self) -> None:
        """Set the default headers for this handler."""
        super().set_headers()
        if not sys.flags.dev_mode and "v" in self.request.arguments:
            self.set_header(  # never changes
                "Cache-Control",
                f"public, immutable, min-fresh={10 * 365 * 24 * 60 * 60}",
            )

    def compute_etag(self) -> None | str:
        """Don't compute etag, because it isn't necessary."""
        return None
