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

import hashlib
import subprocess

from .. import DIR
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def run_cmd(cmd: str) -> str:
    """Run a command in a subprocess."""
    try:
        return subprocess.run(
            cmd,
            cwd=DIR,
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return ""


VERSION = run_cmd("git rev-parse HEAD").strip()
FILE_HASHES = run_cmd("git ls-files | xargs sha1sum")
HASH_OF_FILE_HASHES = hashlib.sha1(FILE_HASHES.encode("utf-8")).hexdigest()
GH_PAGES_COMMIT_HASH = run_cmd("git rev-parse origin/gh-pages")


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/version/?", Version),
            (r"/api/version/?", VersionAPI),
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

    async def get(self) -> None:
        """Handle the GET request to the version page."""
        await self.render(
            "pages/version.html",
            version=VERSION,
            file_hashes=FILE_HASHES,
            hash_of_file_hashes=HASH_OF_FILE_HASHES,
            gh_pages_commit_hash=GH_PAGES_COMMIT_HASH,
        )
