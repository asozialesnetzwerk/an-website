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
import io
import os
import sys
from queue import SimpleQueue
from tempfile import NamedTemporaryFile, TemporaryDirectory
from threading import Thread
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
        self.dir = TemporaryDirectory()
        self.file = NamedTemporaryFile(dir=self.dir.name, delete=False)
        self.queue = SimpleQueue()
        self.thread = Thread(
            target=write_from_queue, args=(self.file, self.queue), daemon=True
        )
        self.thread.start()

    def data_received(self, chunk: bytes) -> None:
        self.queue.put(chunk)

    def on_finish(self) -> None:
        self.queue.put(None)

    async def put(self, filename: str) -> None:
        """Handle the PUT request to the update API."""
        self.queue.put(None)
        while not self.queue.empty():  # pylint: disable=while-used
            await asyncio.sleep(0)
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
