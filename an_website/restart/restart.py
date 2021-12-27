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

"""The restart API used to restart and update the page."""
from __future__ import annotations

import os
import re

from tornado.web import HTTPError

from an_website import DIR as AN_WEBSITE_DIR

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, run


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/restart/", Restart),),
        name="Restart-API",
        description="Restart-API, die genutzt wird um die Seite neu "
        "zu starten",
        path="/api/restart/",
        hidden=True,
    )


class Restart(APIRequestHandler):
    """The Tornado request handler for the restart API."""

    ALLOWED_METHODS: tuple[str, ...] = ("POST",)
    REQUIRES_AUTHORIZATION: bool = True

    async def post(self) -> None:
        """Handle the POST request to the restart API."""
        commit: str = str(
            self.get_query_argument("commit", default=str(), strip=True)
        )

        # check if commit only contains valid letters and numbers
        # used to protect against code execution
        if re.search("[^0-9a-f]", commit) is not None:
            raise HTTPError(
                400, reason="Commit can only contain letters and numbers."
            )

        # git commits are always 40 chars long
        if len(commit) not in (40, 0):
            raise HTTPError(400, reason="Commit has to be 40 chars long.")

        # get the parent dir of the an_website module dir
        repo_path = os.path.dirname(AN_WEBSITE_DIR)

        # check if restart script exists:
        if not os.path.isfile(os.path.join(repo_path, "restart.sh")):
            raise HTTPError(501)

        # execute the restarting script
        code, stdout, stderr = await run(
            "sh",
            "-c",
            f"cd {repo_path} ; ./restart.sh '{commit}' 'no_restart'",
        )

        if not code:
            await self.finish(
                {"status": 200, "reason": "Successful. Restarting now."}
            )
            raise KeyboardInterrupt  # exit so supervisord will restart

        raise HTTPError(
            401,
            reason=f"restart.sh exited with code={code!r}, "
            f"stdout='{stdout!r}' and stderr='{stderr!r}'",
        )
