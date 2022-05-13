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

"""This module provides a request handler that serves the Elastic RUM Agent."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urlsplit

from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from .. import DIR as ROOT_DIR
from .request_handler import BaseRequestHandler
from .utils import ModuleInfo

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Datei-Utilities",
        description="Nützliche Werkzeuge für statische Dateien.",
        handlers=(
            (
                r"/@elastic/apm-rum@(.+)/dist/bundles"
                r"/elastic-apm-rum.umd(\.min|).js(\.map|)",
                ElasticRUM,
            ),
        ),
        hidden=True,
    )


class ElasticRUM(BaseRequestHandler):
    """A request handler that serves the Elastic RUM Agent."""

    URL = (
        "https://unpkg.com/@elastic/apm-rum@{}"
        "/dist/bundles/elastic-apm-rum.umd{}.js{}"
    )
    SCRIPTS: dict[str, tuple[str, float]] = {}
    CACHE_TIME = 365 * 60 * 60 * 24

    async def get(
        self,
        version: str,
        spam: str = "",
        eggs: str = "",
        *,
        # pylint: disable=unused-argument
        head: bool = False,
    ) -> None:
        """Serve the RUM script."""
        key = version + spam + eggs
        if key not in self.SCRIPTS or self.SCRIPTS[key][1] < time.monotonic():
            response = await AsyncHTTPClient().fetch(
                self.URL.format(version, spam, eggs),
                raise_error=False,
                ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
            )
            if response.code != 200:
                raise HTTPError(response.code, reason=response.reason)
            self.SCRIPTS[key] = (
                response.body.decode(),
                time.monotonic() + 365 * 24 * 60 * 60,
            )
            new_path = urlsplit(response.effective_url).path
            if new_path.endswith(".js"):
                BaseRequestHandler.ELASTIC_RUM_JS_URL = new_path
            logger.info("RUM script %s updated", new_path)
            self.redirect(self.fix_url(new_path), False)
            return
        if eggs:  # if serving source map (URL ends with ".map")
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        else:  # if serving JS
            self.set_header(
                "Content-Type", "application/javascript; charset=UTF-8"
            )
            if spam:  # if serving minified JS (URL contains ".min")
                self.set_header(
                    "SourceMap", self.request.full_url().split("?")[0] + ".map"
                )
        self.set_header(
            "Expires", datetime.utcnow() + timedelta(seconds=self.CACHE_TIME)
        )
        self.set_header(
            "Cache-Control", f"public, min-fresh={self.CACHE_TIME}, immutable"
        )
        return await self.finish(self.SCRIPTS[key][0])
