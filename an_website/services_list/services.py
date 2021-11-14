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

"""A page with a list of services that are cool and hosted by us."""
from __future__ import annotations

import dataclasses
from typing import Optional
from urllib.parse import quote

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(("/services-list/", ServicesHandler),),
        name="Service-Liste",
        description="Liste von coolen Services des Asozialen Netzwerks",
        path="/services-list/",
        keywords=("Service", "Liste"),
        aliases=("/services/",),
    )


@dataclasses.dataclass(frozen=True)
class Service:
    """A class representing a service."""

    title: str
    text: str
    infos: Optional[dict[str, str]] = None

    def to_html(self) -> str:
        """Create a html representation of this service and return it."""
        html = [f"<h2>{self.title}</h2>", self.text]

        if self.infos is not None and len(self.infos) > 0:
            html.append("<table>")
            for key, value in self.infos.items():
                if value.startswith("http") and "://" in value:
                    value = (
                        f"<a href='/redirect/?to={quote(value)}"
                        f"&from=/services-list/'>{value}</a>"
                    )
                html.append(f"<tr><td>{key}</td><td>{value}</td></tr>")

            html.append("</table>")

        return "".join(html)


SERVICES: tuple[Service, ...] = (
    Service(
        "Minecraft-Server",
        "Der Survival-Minecraft-Server des Asozialen Netzwerkes funktioniert "
        "auch ohne einen Minecraft-Account und hat dafür eine Integration mit "
        "ely.by, damit auch Spieler, die ihren Minecraft-Account nicht "
        "verraten möchten, einen eigenen Skin nutzen können.",
        {
            "Domain": "minceraft"  # [sic!] Mal gucken ob wer den "typo" meldet
            ".asozial.org",
            "Version": "1.15.2 (1.7-1.16 wird unterstützt)",
            "Karte": "http://minecraft.asozial.org:8123/",
        },
    ),
    Service(
        "SuperTuxKart-Server",
        "Der SuperTuxKart-Server des Asozialen Netzwerkes ist durchgehend "
        "online.",
        {
            "Name": "Das Asoziale Netzwerk",
            "Domain": "stk.asozial.org",
            "SuperTuxKart-Download": "https://supertuxkart.net/Download/",
        },
    ),
    Service(
        "Matrix-Heimserver",
        "Der Matrix-Heimserver des Asozialen Netzwerkes ist zuverlässig und "
        "nutzt im Gegensatz zu den meisten anderen Servern Dendrite anstatt "
        "Synapse. Die Erstellung eines Accounts ist 100 % kostenlos und ohne "
        "E-Mail-Adresse oder Telefonnummer möglich.",
        {
            "Domain": "asozial.org",
            "Matrix-Client": "https://chat.asozial.org/",
        },
    ),
    Service(
        "Syncplay-Server",
        "Mit dem Syncplay-Server des Asozialen Netzwerkes kann man Online "
        "zusammen Sachen gucken.",
        {
            "Domain": "syncplay.asozial.org:8999",
            "Installations-Guide": "https://syncplay.pl/guide/install/",
        },
    ),
)

HTML_LIST: str = "\n".join(service.to_html() for service in SERVICES)


del SERVICES


class ServicesHandler(BaseRequestHandler):
    """The request handler for this page."""

    RATELIMIT_TOKENS = 0

    def get(self):
        """Handle get requests to the service list page."""
        self.render(
            "pages/services.html",
            html=HTML_LIST,
        )
