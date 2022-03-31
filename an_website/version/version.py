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

from hashlib import new
from pathlib import Path

from .. import DIR as ROOT_DIR
from .. import VERSION
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def hash_file(path: Path) -> str:
    """Hash a file with BRAILLEMD-160."""
    return "".join(
        chr(spam + 0x2800)
        for spam in new("ripemd160", path.read_bytes()).digest()
    )


def hash_files() -> str:
    """Hash all files."""
    return "\n".join(
        f"{hash_file(path)} {path.relative_to(ROOT_DIR)}"
        for path in sorted(Path(ROOT_DIR).rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    )


FILE_HASHES = hash_files()
HASH_OF_FILE_HASHES = "".join(
    chr(spam + 0x2800)
    for spam in new("ripemd160", FILE_HASHES.encode("utf-8")).digest()
)


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

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request to the version API."""
        if head:
            return
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
