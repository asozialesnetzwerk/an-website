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
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from http.client import responses
from pathlib import Path
from typing import Any, ClassVar, Final, override
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

        paths: Mapping[str, str] = self.settings.get("NORMED_PATHS") or {}

        if p := paths.get(this_path_normalized):
            return self.redirect(self.fix_url(new_path=p), False)

        if len(this_path_normalized) <= 1:
            return self.redirect(self.fix_url(new_path="/"))

        prefixes = tuple(
            (p, repl)
            for p, repl in paths.items()
            if this_path_normalized.startswith(f"{p}/")
            if f"/{p}" != repl.lower()
            if p != "api"  # api should not be a prefix
        )

        if len(prefixes) == 1:
            ((prefix, replacement),) = prefixes
            return self.redirect(
                self.fix_url(
                    new_path=f"{replacement.strip('/')}"
                    f"{this_path_normalized.removeprefix(prefix)}"
                ),
                False,
            )
        if prefixes:
            LOGGER.error(
                "Too many prefixes %r for path %s", prefixes, self.request.path
            )

        matches = get_close_matches(this_path_normalized, paths, count=1)
        if matches:
            return self.redirect(
                self.fix_url(new_path=paths[matches[0]]), False
            )

        self.set_status(404)
        self.write_error(404)


class ErrorPage(HTMLRequestHandler):
    """A request handler that shows the error page."""

    _success_status: int = 200
    """The status code that is expected to be returned."""

    @override
    def clear(self) -> None:
        """Reset all headers and content for this response."""
        super().clear()
        self._success_status = 200

    @override
    async def get(self, code: str, *, head: bool = False) -> None:
        """Show the error page."""
        # pylint: disable=unused-argument
        status_code = int(code)
        reason = (
            "Nice Try" if status_code == 469 else responses.get(status_code, "")
        )
        # set the status code if it is allowed
        if status_code not in (204, 304) and not 100 <= status_code < 200:
            self.set_status(status_code, reason)
            self._success_status = status_code
        return await self.render(
            "error.html",
            status=status_code,
            reason=reason,
            description=self.get_error_page_description(status_code),
            is_traceback=False,
        )

    @override
    def get_status(self) -> int:
        """Hack the status code.

        This hacks the status code to be 200 if the status code is expected.
        This avoids sending error logs to APM or Webhooks in case of success.

        This depends on the fact that Tornado internally uses self._status_code
        to set the status code in the response and self.get_status() when
        deciding how to log the request.
        """
        status = super().get_status()
        if status == self._success_status:
            return 200
        return status


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
