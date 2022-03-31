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
The API (currently) used to restart and update the page.

Will be removed soon.
"""

from __future__ import annotations

import os
import re

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permissions, run


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/restart", Restart),),
        name="Restart-API",
        description="Restart-API, die genutzt wird um die Seite neu zu starten",
        path="/api/restart",
        aliases=("/api/neustart",),
        hidden=True,
    )


class Restart(APIRequestHandler):
    """The request handler for the restart API."""

    ALLOWED_METHODS: tuple[str, ...] = ("POST",)
    REQUIRED_PERMISSION: Permissions = Permissions.UPDATE

    async def post(self) -> None:
        """Handle the POST request to the restart API."""
        commit: str = str(self.get_argument("commit", default="", strip=True))

        # check that commit hash only contains letters and numbers
        # used to protect against ACE
        if re.search("[^0-9a-f]", commit) is not None:
            raise HTTPError(
                400, reason="Commit-Hash can only contain letters and numbers."
            )

        # git commit hashes are always 40 characters long
        if len(commit) not in (40, 0):
            raise HTTPError(
                400, reason="Commit-Hash has to be 40 characters long."
            )

        repo_path = "/home/an-website/an-website"

        # check if update script exists
        if not os.path.isfile(os.path.join(repo_path, "update.sh")):
            raise HTTPError(503)

        # execute the update script
        code, stdout, stderr = await run(
            os.path.join(repo_path, "update.sh"),
            f"{commit}",
            "no_restart",
            cwd=repo_path,
        )

        if not code:
            await self.finish(
                {"status": 200, "reason": "Successful. Restarting now."}
            )
            raise KeyboardInterrupt  # exit so supervisord will restart

        raise HTTPError(
            500,
            reason=(
                f"update.sh exited with code={code!r}, "
                f"stdout='{stdout!r}' and stderr='{stderr!r}'"
            ),
        )
