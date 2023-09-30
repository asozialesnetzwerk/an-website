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

"""
Useful request handlers used by other modules.

This should only contain request handlers and the get_module_info function.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from http.client import responses
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Final
from urllib.parse import unquote, urlsplit

import regex
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from .. import DIR as ROOT_DIR
from .base_request_handler import BaseRequestHandler
from .utils import (
    SUS_PATHS,
    get_close_matches,
    remove_suffix_ignore_case,
    replace_umlauts,
)

if TYPE_CHECKING or sys.hexversion >= 0x30C00A6:
    # pylint: disable=no-name-in-module, ungrouped-imports
    from typing import override
else:
    from typing_extensions import override

LOGGER: Final = logging.getLogger(__name__)


class HTMLRequestHandler(BaseRequestHandler):
    """A request handler that serves HTML."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "text/html",
        "text/plain",
        "text/markdown",
        "application/vnd.asozial.dynload+json",
    )


class APIRequestHandler(BaseRequestHandler):
    """The base API request handler."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "application/json",
        "application/yaml",
    )


class NotFoundHandler(BaseRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    @override
    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing to have default title and description."""
        if "module_info" not in kwargs:
            kwargs["module_info"] = None
        super().initialize(*args, **kwargs)

    @override
    async def prepare(self) -> None:
        """Throw a 404 HTTP error or redirect to another page."""
        self.now = await self.get_time()

        if self.request.method not in {"GET", "HEAD"}:
            raise HTTPError(404)

        new_path = regex.sub(r"/+", "/", self.request.path.rstrip("/")).replace(
            "_", "-"
        )

        for ext in (".html", ".htm", ".php"):
            new_path = remove_suffix_ignore_case(new_path, f"/index{ext}")
            new_path = remove_suffix_ignore_case(new_path, ext)

        new_path = replace_umlauts(new_path)

        if new_path.lower() in SUS_PATHS:
            self.set_status(469, reason="Nice Try")
            return self.write_error(469)

        if new_path != self.request.path:
            return self.redirect(self.fix_url(new_path=new_path), True)

        this_path_normalized = unquote(new_path).strip("/").lower()

        if len(this_path_normalized) == 1:
            return self.redirect(self.fix_url(new_path="/"))

        paths: tuple[str, ...] = self.settings.get("NORMED_PATHS") or ()
        matches = get_close_matches(this_path_normalized, paths, count=1)
        if matches:
            return self.redirect(self.fix_url(new_path=matches[0]), False)

        self.set_status(404)
        self.write_error(404)


class ErrorPage(HTMLRequestHandler):
    """A request handler that shows the error page."""

    @override
    async def get(self, code: str) -> None:
        """Show the error page."""
        status_code = int(code)
        reason = (
            "Nice Try" if status_code == 469 else responses.get(status_code, "")
        )
        # set the status code if it is allowed
        if status_code not in (204, 304) and not 100 <= status_code < 200:
            self.set_status(status_code, reason)
        return await self.render(
            "error.html",
            status=status_code,
            reason=reason,
            description=self.get_error_page_description(status_code),
            is_traceback=False,
        )


class ZeroDivision(BaseRequestHandler):
    """A request handler that raises an error."""

    @override
    async def prepare(self) -> None:
        """Divide by zero and raise an error."""
        self.now = await self.get_time()
        self.handle_accept_header(self.POSSIBLE_CONTENT_TYPES)
        if self.request.method != "OPTIONS":
            420 / 0  # pylint: disable=pointless-statement


class ElasticRUM(BaseRequestHandler):
    """A request handler that serves the Elastic RUM Agent."""

    POSSIBLE_CONTENT_TYPES = (
        "application/javascript",
        "application/json",
        "text/javascript",  # RFC 9239 (6)
    )

    URL: ClassVar[str] = (
        "https://unpkg.com/@elastic/apm-rum@{}"
        "/dist/bundles/elastic-apm-rum.umd{}.js{}"
    )

    SCRIPTS: ClassVar[dict[str, bytes]] = {}

    @override
    async def get(
        self,
        version: str,
        spam: str = "",
        eggs: str = "",
        *,
        head: bool = False,
    ) -> None:
        """Serve the RUM script."""
        self.handle_accept_header(
            ("application/json",)
            if eggs
            else ("application/javascript", "text/javascript")
        )

        # pylint: disable=redefined-outer-name
        if (key := version + spam + eggs) not in self.SCRIPTS and not head:
            response = await AsyncHTTPClient().fetch(
                self.URL.format(version, spam, eggs),
                raise_error=False,
                ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
            )
            if response.code != 200:
                raise HTTPError(response.code, reason=response.reason)
            self.SCRIPTS[key] = response.body
            new_path = urlsplit(response.effective_url).path
            if new_path.endswith(".js"):
                BaseRequestHandler.ELASTIC_RUM_URL = new_path
            LOGGER.info("RUM script %s updated", new_path)
            self.redirect(self.fix_url(new_path), False)
            return

        if spam and not eggs:  # if serving minified JS (URL contains ".min")
            self.set_header(
                "SourceMap", self.request.full_url().split("?")[0] + ".map"
            )

        self.set_header(
            "Expires", datetime.now(timezone.utc) + timedelta(days=365)
        )
        self.set_header(
            "Cache-Control",
            f"public, immutable, max-age={60 * 60 * 24 * 365}",
        )

        return await self.finish(self.SCRIPTS[key] or b"")


for key, file in {
    "5.12.0": "elastic-apm-rum.umd.js",
    "5.12.0.min": "elastic-apm-rum.umd.min.js",
    "5.12.0.min.map": "elastic-apm-rum.umd.min.js.map",
}.items():
    path = Path(ROOT_DIR) / "vendored" / "apm-rum" / file
    ElasticRUM.SCRIPTS[key] = path.read_bytes()

del key, file, path  # type: ignore[possibly-undefined]  # pylint: disable=undefined-loop-variable  # noqa: B950
