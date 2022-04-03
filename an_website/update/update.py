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

"""The API used to update the page."""

from __future__ import annotations

import asyncio
import os
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any
from urllib.parse import unquote

from tornado.web import stream_request_body

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permissions


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/update/(.*)", UpdateAPI),),
        name="Update-API",
        description="Update-API, die genutzt wird um die Seite zu aktualisieren",
        path="/api/update",
        hidden=True,
    )


@stream_request_body
class UpdateAPI(APIRequestHandler):
    """The request handler for the update API."""

    ALLOWED_METHODS: tuple[str, ...] = ("PUT",)
    REQUIRED_PERMISSION: Permissions = Permissions.UPDATE

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the request handler."""
        # pylint: disable=attribute-defined-outside-init, consider-using-with
        super().initialize(*args, **kwargs)
        self.dir = TemporaryDirectory()
        self.file = NamedTemporaryFile(dir=self.dir.name, delete=False)

    def data_received(self, chunk: bytes) -> None:
        """Write received data."""
        self.file.write(chunk)

    async def put(self, filename: str) -> None:
        """Handle the PUT request to the update API."""
        self.file.close()
        filepath = os.path.join(self.dir.name, unquote(filename))
        os.rename(self.file.name, filepath)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "install",
            "--require-virtualenv",
            filepath,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        self.set_status(202)
        # pylint: disable=while-used
        while not process.stdout.at_eof():  # type: ignore[union-attr]
            output = await process.stdout.readline()  # type: ignore[union-attr]
            self.write(output)
            self.flush()
        await self.finish()
        await process.wait()
        if not process.returncode:
            raise KeyboardInterrupt
