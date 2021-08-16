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

"""The restart api used to restart and update the page."""
from __future__ import annotations

import os

from tornado.web import HTTPError

from an_website import DIR as AN_WEBSITE_DIR

from ..utils.utils import APIRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/restart/?", Restart),),
        name="Restart-Api",
        description="Restart-Api, die genutzt wird um die Seite neuzustarten.",
    )


class Restart(APIRequestHandler):
    """The tornado request handler for the restart api."""

    async def get(self):
        """Handle the get request to the restart api."""
        secret = self.request.headers.get("Authorization")

        api_secrets = self.settings.get("API_SECRETS")
        if api_secrets is None or len(api_secrets) == 0:
            raise HTTPError(501)

        if secret not in api_secrets:
            raise HTTPError(401)

        commit = self.get_query_argument("commit", default="", strip=True)

        # get the parent dir of the an_website module dir
        command_dir = os.path.dirname(AN_WEBSITE_DIR)

        code = os.system(f"cd {command_dir} ; sh -c 'restart.sh {commit}'")

        if code != 0:
            raise HTTPError(500)
