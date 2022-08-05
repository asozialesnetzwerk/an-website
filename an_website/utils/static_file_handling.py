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
    return {
        str(path).removeprefix(ROOT_DIR): hash_file(path)
        for path in Path(STATIC_DIR).rglob("*")
        if path.is_file() and "img/openmoji-svg-" not in str(path)
    }


FILE_HASHES_DICT = create_file_hashes_dict()

# https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
# modified to add ATOM, RSS, and WASM
CONTENT_TYPES = {
    "3g2": "video/3gpp2",
    "3gp": "video/3gpp",
    "7z": "application/x-7z-compressed",
    "aac": "audio/aac",
    "abw": "application/x-abiword",
    "arc": "application/x-freearc",
    "atom": "application/atom+xml",
    "avi": "video/x-msvideo",
    "avif": "image/avif",
    "azw": "application/vnd.amazon.ebook",
    "bin": "application/octet-stream",
    "bmp": "image/bmp",
    "bz": "application/x-bzip",
    "bz2": "application/x-bzip2",
    "cda": "application/x-cdf",
    "csh": "application/x-csh",
    "css": "text/css",
    "csv": "text/csv",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "eot": "application/vnd.ms-fontobject",
    "epub": "application/epub+zip",
    "gif": "image/gif",
    "gz": "application/gzip",
    "htm": "text/html",
    "html": "text/html",
    "ico": "image/vnd.microsoft.icon",
    "ics": "text/calendar",
    "jar": "application/java-archive",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "js": "text/javascript",
    "json": "application/json",
    "jsonld": "application/ld+json",
    "mid": "audio/midi",
    "midi": "audio/midi",
    "mjs": "text/javascript",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "mpeg": "video/mpeg",
    "mpkg": "application/vnd.apple.installer+xml",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odt": "application/vnd.oasis.opendocument.text",
    "oga": "audio/ogg",
    "ogv": "video/ogg",
    "ogx": "application/ogg",
    "opus": "audio/opus",
    "otf": "font/otf",
    "pdf": "application/pdf",
    "php": "application/x-httpd-php",
    "png": "image/png",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "rar": "application/vnd.rar",
    "rss": "application/rss+xml",
    "rtf": "application/rtf",
    "sh": "application/x-sh",
    "svg": "image/svg+xml",
    "swf": "application/x-shockwave-flash",
    "tar": "application/x-tar",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "ts": "video/mp2t",
    "ttf": "font/ttf",
    "txt": "text/plain",
    "vsd": "application/vnd.visio",
    "wasm": "application/wasm",
    "wav": "audio/wav",
    "weba": "audio/webm",
    "webm": "video/webm",
    "webp": "image/webp",
    "woff": "font/woff",
    "woff2": "font/woff2",
    "xhtml": "application/xhtml+xml",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xml": "application/xml",
    "xul": "application/vnd.mozilla.xul+xml",
    "zip": "application/zip",
}


def get_handlers() -> list[Handler]:
    """Return a list of handlers for static files."""
    handlers: list[Handler] = [
        (
            r"/(?:static/)?(\.env|favicon\.png|humans\.txt|robots\.txt)",
            StaticFileHandler,
            {"path": STATIC_DIR},
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
    if url.startswith("/static/img/openmoji-svg-"):
        return url
    if url in FILE_HASHES_DICT:
        hash_ = FILE_HASHES_DICT[url]
        if url == "/static/favicon.png":
            return f"/favicon.png?v={hash_}"
        return f"{url}?v={hash_}"
    logger.warning("%s not in FILE_HASHES_DICT", url)
    return url


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
            if self.content_type.startswith("text/"):  # RFC2616 3.7.1
                self.set_header(
                    "Content-Type", f"{self.content_type};charset=utf-8"
                )
            else:
                self.set_header("Content-Type", self.content_type)

    def validate_absolute_path(
        self, root: str, absolute_path: str
    ) -> None | str:
        """Validate the path and detect the content type."""
        if (
            path := super().validate_absolute_path(root, absolute_path)
        ) and not self.content_type:
            self.content_type = CONTENT_TYPES.get(path.rsplit(".", 1)[-1])
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
    def make_static_url(
        cls, settings: dict[str, Any], path: str, include_version: bool = True
    ) -> str:
        """Make a static url for the given path."""
        return fix_static_url(path)

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
                f"public, immutable, min-fresh={10 * 365 * 24 * 60 * 60}",
            )
