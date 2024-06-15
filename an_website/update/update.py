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
import logging
import os
import sys
from asyncio import Future
from queue import SimpleQueue
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import IO, TYPE_CHECKING, Any, ClassVar, Final
from urllib.parse import unquote

from tornado.web import stream_request_body

from .. import EVENT_SHUTDOWN, NAME
from ..utils.decorators import requires
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permission

if TYPE_CHECKING:
    from tempfile import _TemporaryFileWrapper

LOGGER: Final = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/update/(.*)", UpdateAPI),),
        name="Update-API",
        description=f"API zum Aktualisieren von {NAME.removesuffix('-dev')}",
        hidden=True,
    )


def write_from_queue(file: IO[bytes], queue: SimpleQueue[None | bytes]) -> None:
    """Read from a queue and write to a file."""
    while (chunk := queue.get()) is not None:  # pylint: disable=while-used
        file.write(chunk)
    file.flush()


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
            char = await process.stdout.read(1)  # type: ignore[union-attr]
            self.write(char)
            if char == b"\n":
                self.flush()  # type: ignore[unused-awaitable]
        await process.wait()
        assert process.returncode is not None
        return process.returncode

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
        self.file.close()

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
