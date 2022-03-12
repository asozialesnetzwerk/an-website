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

"""The version page of the website."""

from __future__ import annotations

from pathlib import Path

from blake3 import blake3  # type: ignore

from .. import DIR as ROOT_DIR
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, hash_file, run_shell_cmd


def hash_files() -> str:
    """Hash all the files."""
    return "\n".join(
        f"{hash_file(path)} {path.relative_to(ROOT_DIR)}"
        for path in sorted(Path(ROOT_DIR).rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    )


VERSION = run_shell_cmd("git rev-parse HEAD").strip()
FILE_HASHES = hash_files()
HASH_OF_FILE_HASHES = blake3(FILE_HASHES.encode("utf-8")).hexdigest()


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/version", Version),
            (r"/api/version", VersionAPI),
        ),
        name="Versions-Informationen",
        description="Die aktuelle Version der Webseite",
        path="/version",
        keywords=(
            "Version",
            "aktuell",
        ),
        hidden=True,
    )


class VersionAPI(APIRequestHandler):
    """The Tornado request handler for the version API."""

    async def get(self) -> None:
        """Handle the GET request to the version API."""
        return await self.finish(
            {
                "version": VERSION,
                "hash": HASH_OF_FILE_HASHES,
            }
        )


class Version(HTMLRequestHandler):
    """The Tornado request handler for the version page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request to the version page."""
        if head:
            return
        await self.render(
            "pages/version.html",
            version=VERSION,
            file_hashes=FILE_HASHES,
            hash_of_file_hashes=HASH_OF_FILE_HASHES,
        )
