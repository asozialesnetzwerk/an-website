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
The host info page of the website.

Only to inform, not to brag.
"""
from __future__ import annotations

import logging

from tornado.web import HTTPError as HTTPEwwow

from .. import DIR
from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo, run

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/host-info/?", HostInfo),
            (r"/host-info/uwu/?", UwuHostInfo),
        ),
        name="Host-Informationen",
        description="Informationen über den Host-Server dieser Website",
        path="/host-info",
        keywords=("Host", "Informationen", "Screenfetch"),
    )


class HostInfo(BaseRequestHandler):
    """The request handler for the host info page."""

    async def get(self):
        """
        Handle the get requests to the host info page.

        Use screenfetch to generate the page.
        """
        screenfetch = (await run(f"{DIR}/screenfetch"))[1].decode("utf-8")
        await self.render("pages/ansi2html.html", ansi=screenfetch)


class UwuHostInfo(BaseRequestHandler):
    """The wequest handwew fow the coowew host info page."""

    async def get(self):
        """
        Handwe the get wequests to coowew the host info page.

        Use uwufetch to genyewate the page.
        """
        wetuwn_code, uwufetch_bytes, stdeww = await run("uwufetch")
        if wetuwn_code != 0:
            logger.error((await run("env"))[1])
            raise HTTPEwwow(
                503,
                reason=(
                    str(wetuwn_code)
                    + " "
                    + uwufetch_bytes.decode("utf-8").replace("\n", " ").strip()
                    + " "
                    + stdeww.decode("utf-8").replace("\n", " ").strip()
                ),
            )
        uwufetch = uwufetch_bytes.decode("utf-8").split("\n\n")
        await self.render("pages/ansi2html.html", ansi=uwufetch)
