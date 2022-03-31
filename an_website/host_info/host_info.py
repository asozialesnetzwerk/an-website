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
import os
import re
import sys

from tornado.web import HTTPError as HTTPEwwow

from .. import DIR as ROOT_DIR
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo, PageInfo, run, str_to_bool

logger = logging.getLogger(__name__)

SCREENFETCH_PATH = os.path.join(ROOT_DIR, "screenfetch")


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/host-info", HostInfo),
            (r"/host-info/uwu", UwUHostInfo),
        ),
        name="Host-Informationen",
        description="Informationen über den Host-Server dieser Webseite",
        path="/host-info",
        sub_pages=(
            PageInfo(
                name="Howost-Infowmationyen",
                description=(
                    "Infowmationyen übew den Howost-Sewvew diesew W-Webseite"
                ),
                path="/host-info/uwu",
                keywords=("UWU",),
                hidden=True,
            ),
        ),
        keywords=("Host", "Informationen", "Screenfetch"),
    )


def minify_ansi_art(string: str) -> str:
    """Minify an ANSI art string."""
    return re.sub(
        r"(?m)\s+\x1B\[0m$", "\x1B[0m", string
    )  # for arch: 1059 → 898


class HostInfo(HTMLRequestHandler):
    """The request handler for the host info page."""

    RATELIMIT_GET_LIMIT = 5

    SCREENFETCH_CACHE: dict[str, str] = {}

    async def get(self, *, head: bool = False) -> None:
        """
        Handle the GET requests to the host info page.

        Use screenFetch to generate the page.
        """
        if head:
            return
        if "LOGO" not in self.SCREENFETCH_CACHE:
            self.SCREENFETCH_CACHE["LOGO"] = minify_ansi_art(
                (await run(SCREENFETCH_PATH, "-L"))[1].decode("utf-8")
            )

        await self.render(
            "ansi2html.html",
            ansi=[
                self.SCREENFETCH_CACHE["LOGO"],
                (await run(SCREENFETCH_PATH, "-n"))[1].decode("utf-8"),
            ],
            powered_by="https://github.com/KittyKatt/screenFetch",
            powered_by_name="screenFetch",
        )


class UwUHostInfo(HTMLRequestHandler):
    """The wequest handwew fow the coowew host info page."""

    RATELIMIT_GET_LIMIT = 5

    async def get(self, *, head: bool = False) -> None:
        """
        Handwe the GET wequests to coowew the host info page.

        Use UwUFetch to genyewate the page.
        """
        if head:
            cache_enabwed = 1
        else:
            cache_disabwed = self.get_query_argument(
                "cache_disabled", default=""
            )
            cache_enabwed = (
                0 if str_to_bool(cache_disabwed, default=False) else 1
            )

        wetuwn_code, uwufetch_bytes, _ = await run(
            "env",
            f"SHELL=python{sys.version.split(' ', maxsplit=1)[0]}",
            f"UWUFETCH_CACHE_ENABLED={cache_enabwed}",
            "uwufetch",
            "-w",
        )
        if wetuwn_code == 127:
            raise HTTPEwwow(
                503,
                reason="Sowwy. This sewvew h-hasn't instawwed UwUFetch.",
            )
        if wetuwn_code:
            raise HTTPEwwow(
                500,
                reason=f"UwUFetch has exited with wetuwn code {wetuwn_code}.",
            )
        if head:
            return
        uwufetch = uwufetch_bytes.decode("utf-8").split("\n\n")
        await self.render(
            "ansi2html.html",
            ansi=uwufetch,
            powered_by="https://github.com/TheDarkBug/uwufetch",
            powered_by_name="UwUFetch",
        )
