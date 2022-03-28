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

"""The page that tells users their ip."""

from __future__ import annotations

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/ip", IP),
            (r"/api/ip", IPAPI),
        ),
        name="IP-Informationen",
        description="Erfahre deine IP-Adresse",
        path="/ip",
        keywords=(
            "IP-Adresse",
            "Was ist meine IP?",
        ),
    )


class IPAPI(APIRequestHandler):
    """The Tornado request handler for the IP API."""

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request to the IP API."""
        if head:
            return
        geoip = await self.geoip()
        if geoip:
            return await self.finish(
                {
                    "ip": self.request.remote_ip,
                    "country": geoip.get("country_flag"),
                }
            )
        return await self.finish({"ip": self.request.remote_ip})


class IP(HTMLRequestHandler):
    """The Tornado request handler for the IP page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request to the IP page."""
        if head:
            return
        if not self.request.remote_ip:
            return await self.render(
                "pages/empty.html",
                text="IP-Adresse konnte nicht ermittelt werden.",
            )
        await self.render(
            "pages/empty.html",
            text=(
                "Deine IP-Adresse ist "
                + self.request.remote_ip
                + " "
                + (
                    "🏴‍☠️"
                    if self.request.remote_ip in {"127.0.0.1", "::1"}
                    else (await self.geoip() or {}).get("country_flag") or ""
                )
            ).strip(),
        )
