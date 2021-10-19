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
import sys

from tornado.web import HTTPError as HTTPEwwow

from .. import DIR
from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo, PageInfo, run, str_to_bool

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/host-info/", HostInfo),
            (r"/host-info/uwu/", UwuHostInfo),
        ),
        name="Host-Informationen",
        description="Informationen über den Host-Server dieser Webseite",
        path="/host-info/",
        sub_pages=(
            PageInfo(
                name="Howost-Infowmationyen",
                description="Infowmationyen übew den Howost-Sewvew "
                "diesew W-Webseite",
                path="/host-info/uwu/",
                keywords=("UWU",),
                hidden=True,
            ),
        ),
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
        await self.render(
            "pages/ansi2html.html",
            ansi=screenfetch,
            powered_by="https://github.com/KittyKatt/screenFetch",
            powered_by_name="screenFetch",
        )


class UwuHostInfo(BaseRequestHandler):
    """The wequest handwew fow the coowew host info page."""

    async def get(self):
        """
        Handwe the get wequests to coowew the host info page.

        Use uwufetch to genyewate the page.
        """
        cache_disabwed = self.get_query_argument("cache_disabled", default="")
        cache_enabwed = 0 if str_to_bool(cache_disabwed, default=False) else 1

        wetuwn_code, uwufetch_bytes, _ = await run(
            "env",
            f"SHELL=python{sys.version.split(' ', maxsplit=1)[0]}",
            f"UWUFETCH_CACHE_ENABLED={cache_enabwed}",
            "uwufetch",
            "-w",
        )
        if wetuwn_code != 0:
            raise HTTPEwwow(
                501,
                reason="Sowwy. This sewvew h-hasn't instawwed uwufetch.",
            )
        uwufetch = uwufetch_bytes.decode("utf-8").split("\n\n")
        await self.render(
            "pages/ansi2html.html",
            ansi=uwufetch,
            powered_by="https://github.com/TheDarkBug/uwufetch",
            powered_by_name="UwUFetch",
        )
