# This file is based on the StaticFileHandler from Tornado
# Source: https://github.com/tornadoweb/tornado/blob/b3f2a4bb6fb55f6b1b1e890cdd6332665cfe4a75/tornado/web.py  # noqa: B950  # pylint: disable=line-too-long
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A static file handler for the Traversable abc."""
from __future__ import annotations

import contextlib
import logging
import sys
from collections.abc import Awaitable, Iterable, Mapping, Sequence
from importlib.resources.abc import Traversable
from types import MappingProxyType
from typing import Any, Final, Literal, override
from urllib.parse import urlsplit, urlunsplit

from tornado import httputil, iostream
from tornado.web import GZipContentEncoding, HTTPError
from typed_stream import Stream

from an_website.utils.utils import size_of_file

from .base_request_handler import _RequestHandler
from .static_file_handling import content_type_from_path

type Encoding = Literal["gz", "zst"]

LOGGER: Final = logging.getLogger(__name__)

ENCODINGS: Final[Sequence[tuple[str, Encoding]]] = (
    # better first
    ("zstd", "zst"),
    ("gzip", "gz"),
)
REVERSE_ENCODINGS_MAP: Mapping[Encoding, str] = {
    value: key for key, value in ENCODINGS
}


class TraversableStaticFileHandler(_RequestHandler):
    """A static file handler for the Traversable abc."""

    root: Traversable
    file_hashes: Mapping[str, str] = {}
    headers: Iterable[tuple[str, str]] = ()

    @override
    def compute_etag(self) -> None | str:
        """Return a pre-computed ETag."""
        return self.file_hashes.get(self.request.path)

    async def get(self, path: str, *, head: bool = False) -> None:  # noqa: C901
        # pylint: disable=too-complex, too-many-branches
        """Handle GET requests for files in the static file directory."""
        if self.request.path.endswith("/"):
            self.replace_path_with_redirect(self.request.path.rstrip("/"))
            return

        if path.startswith("/") or ".." in path.split("/") or "//" in path:
            raise HTTPError(404)

        absolute_path, encoding = self.get_absolute_path_encoded(path)

        if not absolute_path.is_file():
            if self.get_absolute_path(path.lower()).is_file():
                if self.request.path.endswith(path):
                    self.replace_path_with_redirect(
                        self.request.path.removesuffix(path) + path.lower()
                    )
                    return
                LOGGER.error(
                    "Failed to fix casing of %s", self.request.full_url()
                )
            raise HTTPError(404)

        self.set_header("Accept-Ranges", "bytes")

        if encoding:
            self.set_header("Content-Encoding", REVERSE_ENCODINGS_MAP[encoding])
        if content_type := self.get_content_type(
            path, self.get_absolute_path(path)
        ):
            self.set_header("Content-Type", content_type)
        del path

        request_range = None
        range_header = self.request.headers.get("Range")
        if range_header:
            # As per RFC 2616 14.16, if an invalid Range header is specified,
            # the request will be treated as if the header didn't exist.
            # pylint: disable-next=protected-access
            request_range = httputil._parse_request_range(range_header)

        size: int = size_of_file(absolute_path)

        if request_range:
            start, end = request_range
            if start is not None and start < 0:
                start += size
                start = max(start, 0)
            if (
                start is not None
                and (start >= size or (end is not None and start >= end))
            ) or end == 0:  # pylint: disable=use-implicit-booleaness-not-comparison-to-zero # noqa: B950
                # As per RFC 2616 14.35.1, a range is not satisfiable only: if
                # the first requested byte is equal to or greater than the
                # content, or when a suffix with length 0 is specified.
                # https://tools.ietf.org/html/rfc7233#section-2.1
                # A byte-range-spec is invalid if the last-byte-pos value is present
                # and less than the first-byte-pos.
                self.set_status(416)  # Range Not Satisfiable
                self.set_header("Content-Type", "text/plain")
                self.set_header("Content-Range", f"bytes */{size}")
                return
            if end is not None and end > size:
                # Clients sometimes blindly use a large range to limit their
                # download size; cap the endpoint at the actual file size.
                end = size
            # Note: only return HTTP 206 if less than the entire range has been
            # requested. Not only is this semantically correct, but Chrome
            # refuses to play audio if it gets an HTTP 206 in response to
            # ``Range: bytes=0-``.
            if size != (end or size) - (start or 0):
                self.set_status(206)  # Partial Content
                self.set_header(
                    "Content-Range",
                    # pylint: disable-next=protected-access
                    httputil._get_content_range(start, end, size),
                )
        else:
            start = end = None

        content_length = len(range(size)[start:end])
        self.set_header("Content-Length", content_length)

        if head:
            assert self.request.method == "HEAD"
            await self.finish()
            return

        for chunk in self.get_content(absolute_path, start=start, end=end):
            self.write(chunk)
            try:
                await self.flush()
            except iostream.StreamClosedError:
                return

        with contextlib.suppress(iostream.StreamClosedError):
            await self.finish()

    def get_absolute_path(self, path: str) -> Traversable:
        """Get the absolute path of a file."""
        return self.root / path

    def get_absolute_path_encoded(
        self, path: str
    ) -> tuple[Traversable, Encoding | None]:
        """Get the absolute path and the encoding."""
        for transform in self._transforms:
            if isinstance(transform, GZipContentEncoding):
                # pylint: disable=protected-access
                transform._gzipping = False

        accepted_encodings: frozenset[str] = (
            Stream(self.request.headers.get_list("Accept-Encoding"))
            .flat_map(str.split, ",")
            .map(lambda string: string.split(";")[0])  # ignore quality specs
            .map(str.strip)
            .collect(frozenset)
        )

        absolute_path = self.get_absolute_path(path)
        encoding: Encoding | None = None

        for key, encoding in ENCODINGS:
            if key in accepted_encodings:
                compressed_path = self.get_absolute_path(f"{path}.{encoding}")
                if compressed_path.is_file():
                    absolute_path = compressed_path
                    break
            encoding = None  # pylint: disable=redefined-loop-name

        return absolute_path, encoding

    @classmethod
    def get_content(
        cls,
        abspath: Traversable,
        start: int | None = None,
        end: int | None = None,
    ) -> Iterable[bytes]:
        """Read the content of a file in chunks."""
        with abspath.open("rb") as file:
            if start is not None:
                file.seek(start)
            remaining: int | None = (
                (end - (start or 0)) if end is not None else None
            )

            while True:  # pylint: disable=while-used
                chunk_size = 64 * 1024
                if remaining is not None and remaining < chunk_size:
                    chunk_size = remaining
                chunk = file.read(chunk_size)
                if chunk:
                    if remaining is not None:
                        remaining -= len(chunk)
                    yield chunk
                else:
                    assert not remaining
                    return

    @classmethod
    def get_content_type(
        cls, path: str, absolute_path: Traversable
    ) -> str | None:
        """Get the content-type of a file."""
        return content_type_from_path(path, absolute_path)

    def head(self, path: str) -> Awaitable[None]:
        """Handle HEAD requests for files in the static file directory."""
        return self.get(path, head=True)

    def initialize(
        self,
        root: Traversable,
        hashes: Mapping[str, str] = MappingProxyType({}),
        headers: Iterable[tuple[str, str]] = (),
    ) -> None:
        """Initialize this handler with a root directory and file hashes."""
        self.root = root
        self.file_hashes = hashes
        self.headers = headers
        for name, value in headers:
            self.set_header(name, value)
        if not sys.flags.dev_mode:
            self.set_etag_header()

    def replace_path_with_redirect(
        self, new_path: str, *, status: int = 307
    ) -> None:
        """Redirect to the replaced path."""
        scheme, netloc, _, query, _ = urlsplit(self.request.full_url())
        self.redirect(
            urlunsplit(
                (
                    scheme,
                    netloc,
                    new_path,
                    query,
                    "",
                )
            ),
            status=status,
        )

    @override
    def set_default_headers(self) -> None:
        """Set the default headers for this handler."""
        super().set_default_headers()
        for name, value in self.headers:
            self.set_header(name, value)

        if not sys.flags.dev_mode:
            if "v" in self.request.arguments:
                self.set_header(  # never changes
                    "Cache-Control",
                    f"public, immutable, max-age={86400 * 365 * 10}",
                )
            else:
                self.set_etag_header()

    @override
    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Write an error response."""
        self.set_header("Content-Type", "text/plain;charset=utf-8")
        self.write(str(status_code))
        self.write(" ")
        self.write(self._reason)
        self.write("\n")
