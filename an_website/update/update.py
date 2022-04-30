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

"""The API used to update the website."""

from __future__ import annotations

import asyncio
import io
import os
import sys
from queue import SimpleQueue
from tempfile import NamedTemporaryFile, TemporaryDirectory
from urllib.parse import unquote

from tornado.web import stream_request_body

from .. import EVENT_SHUTDOWN, NAME
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permissions


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/update/(.*)", UpdateAPI),),
        name="Update-API",
        description=(
            "Update-API, die genutzt wird, "
            f"um {NAME.removesuffix('-dev')} zu aktualisieren"
        ),
        path="/api/update",
        hidden=True,
    )


def write_from_queue(file: io.IOBase, queue: SimpleQueue[None | bytes]) -> None:
    """Read from a queue and write to a file."""
    while True:  # pylint: disable=while-used

        chunk = queue.get()

        if chunk is None:
            file.close()
            break

        file.write(chunk)


@stream_request_body
class UpdateAPI(APIRequestHandler):
    """The request handler for the update API."""

    ALLOWED_METHODS: tuple[str, ...] = ("PUT",)
    REQUIRED_PERMISSION: Permissions = Permissions.UPDATE

    queue: SimpleQueue[None | bytes]

    async def prepare(self) -> None:
        # pylint: disable=attribute-defined-outside-init, consider-using-with
        await super().prepare()
        loop = asyncio.get_running_loop()
        self.dir = TemporaryDirectory()
        self.file = NamedTemporaryFile(dir=self.dir.name, delete=False)
        self.queue = SimpleQueue()
        self.future = loop.run_in_executor(
            None, write_from_queue, self.file, self.queue
        )

    def data_received(self, chunk: bytes) -> None:
        self.queue.put(chunk)

    def on_finish(self) -> None:
        self.queue.put(None)

    async def put(self, filename: str) -> None:
        """Handle the PUT request to the update API."""
        # pylint: disable=while-used
        self.queue.put(None)
        await self.future
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
        self.set_header("X-Accel-Buffering", "no")
        while not process.stdout.at_eof():  # type: ignore[union-attr]
            self.write(await process.stdout.read(1))  # type: ignore[union-attr]
            self.flush()
        await self.finish()
        await process.wait()
        if not process.returncode:
            EVENT_SHUTDOWN.set()
