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

"""The API for updating the website."""

from __future__ import annotations

import asyncio
import io
import logging
import os
import sys
from asyncio import Future
from queue import SimpleQueue
from tempfile import (  # pylint: disable=import-private-name
    NamedTemporaryFile,
    TemporaryDirectory,
    _TemporaryFileWrapper,
)
from typing import Any, ClassVar, Final, cast
from urllib.parse import unquote

from tornado.web import stream_request_body

from .. import EVENT_SHUTDOWN, NAME
from ..utils.decorators import requires
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permission

LOGGER: Final = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/update/(.*)", UpdateAPI),),
        name="Update-API",
        description=f"API zum Aktualisieren von {NAME.removesuffix('-dev')}",
        path="/api/update",
        hidden=True,
    )


def write_from_queue(file: io.IOBase, queue: SimpleQueue[None | bytes]) -> None:
    """Read from a queue and write to a file."""
    while True:  # pylint: disable=while-used
        if (chunk := queue.get()) is None:
            file.close()
            break
        file.write(chunk)


@stream_request_body
class UpdateAPI(APIRequestHandler):  # pragma: no cover
    """The request handler for the update API."""

    ALLOWED_METHODS: ClassVar[tuple[str, ...]] = ("PUT",)
    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = ("text/plain",)

    dir: TemporaryDirectory[str]
    file: _TemporaryFileWrapper[bytes]
    queue: SimpleQueue[None | bytes]
    future: Future[Any]

    def data_received(self, chunk: bytes) -> None:  # noqa: D102
        self.queue.put(chunk)

    def on_finish(self) -> None:  # noqa: D102
        if hasattr(self, "queue"):
            self.queue.put(None)

    async def pip_install(self, *args: str) -> int:
        """Install something and write the output."""
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "pip",
            "install",
            "--require-virtualenv",
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        # pylint: disable=while-used
        while not process.stdout.at_eof():  # type: ignore[union-attr]
            self.write(await process.stdout.read(1))  # type: ignore[union-attr]
            self.flush()  # type: ignore[unused-awaitable]
        await process.wait()
        return cast(int, process.returncode)

    async def prepare(self) -> None:  # noqa: D102
        await super().prepare()
        loop = asyncio.get_running_loop()
        self.dir = TemporaryDirectory()
        self.file = NamedTemporaryFile(dir=self.dir.name, delete=False)
        self.queue = SimpleQueue()
        self.future = loop.run_in_executor(
            None, write_from_queue, self.file, self.queue
        )

    @requires(Permission.UPDATE)
    async def put(self, filename: str) -> None:
        """Handle PUT requests to the update API."""
        self.queue.put(None)
        await self.future

        filepath = os.path.join(self.dir.name, unquote(filename))
        os.rename(self.file.name, filepath)

        self.set_status(202)
        self.set_header("X-Accel-Buffering", "no")

        await self.pip_install("--upgrade", "pip")

        returncode = await self.pip_install(filepath)

        await self.finish()

        if returncode:
            LOGGER.error("Failed to install %s", filename)
        elif self.get_bool_argument("shutdown", True):
            EVENT_SHUTDOWN.set()
