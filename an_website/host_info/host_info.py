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
import shutil
import sys

from tornado.web import HTTPError as HTTPEwwow

from .. import CONTAINERIZED
from .. import DIR as ROOT_DIR
from .. import NAME
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo, PageInfo, run

logger = logging.getLogger(__name__)

SCREENFETCH_PATH = os.path.join(ROOT_DIR, "screenfetch")
UWUFETCH_PATH = shutil.which("uwufetch")
ENV = {
    "USER": NAME,
    "SHELL": f"python{sys.version.split(' ', maxsplit=1)[0]}",
}


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/host-info", HostInfo),
            (r"/host-info/uwu", UwUHostInfo),
        ),
        name="Host-Informationen",
        short_name="Host-Info",
        description="Informationen über den Host-Server dieser Webseite",
        path="/host-info",
        sub_pages=(
            PageInfo(
                name="Howost-Infowmationyen",
                short_name="Howost-Infow",
                description=(
                    "Infowmationyen übew den Howost-Sewvew diesew W-Webseite"
                ),
                path="/host-info/uwu",
                keywords=("UWU",),
                hidden=CONTAINERIZED or not UWUFETCH_PATH,
            ),
        ),
        keywords=("Host", "Informationen", "Screenfetch"),
        hidden=CONTAINERIZED,
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
                (await run(SCREENFETCH_PATH, "-n", env=ENV))[1].decode("utf-8"),
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
        cache_enabwed = int(
            head or not self.get_bool_argument("cache_disabled", default=False)
        )

        if UWUFETCH_PATH:
            wetuwn_code, uwufetch_bytes, _ = await run(
                UWUFETCH_PATH,
                "-w",
                env={"UWUFETCH_CACHE_ENABLED": str(cache_enabwed), **ENV},
            )

        if not UWUFETCH_PATH or wetuwn_code == 127:
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
