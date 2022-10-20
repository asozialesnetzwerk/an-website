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

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(("/services", ServicesHandler),),
        name="Service-Liste",
        description="Liste von coolen Services des Asozialen Netzwerks",
        path="/services",
        keywords=("Service", "Liste"),
        aliases=("/services-list",),
    )


@dataclasses.dataclass(slots=True)
class Service:
    """A class representing a service."""

    title: str
    text: str
    infos: None | dict[str, str]


SERVICES: tuple[Service, ...] = (
    Service(
        "Minceraft-Server",
        "Der Survival-Minceraft-Server des Asozialen Netzwerks funktioniert "
        "auch ohne einen Minceraft-Account und hat dafür eine Integration mit "
        "ely.by, damit auch Spieler, die ihren Minceraft-Account nicht "
        "verraten möchten, einen eigenen Skin nutzen können.",
        {
            "Domain": "minceraft.asozial.org",
            "Version": "1.15.2 (1.7-1.19 wird unterstützt)",
            "Karte": "https://minceraft.asozial.org",
        },
    ),
    Service(
        "SuperTuxKart-Server",
        "Der SuperTuxKart-Server des Asozialen Netzwerks ist durchgehend "
        "online.",
        {
            "Name": "Das Asoziale Netzwerk",
            "SuperTuxKart-Download": "https://supertuxkart.net/Download",
        },
    ),
    Service(
        "Syncplay-Server",
        "Mit dem Syncplay-Server des Asozialen Netzwerks kann man Online "
        "zusammen Sachen gucken.",
        {
            "Domain": "syncplay.asozial.org:8999",
            "Installations-Guide": "https://syncplay.pl/guide/install",
        },
    ),
    Service(
        "Matrix-Heimserver",
        "Der Matrix-Heimserver des Asozialen Netzwerks ist zuverlässig und "
        "nutzt im Gegensatz zu den meisten anderen Servern Dendrite anstatt "
        "Synapse. Die Erstellung eines Accounts ist 100% kostenlos und ohne "
        "E-Mail-Adresse oder Telefonnummer möglich.",
        {
            "Domain": "asozial.org",
            "Matrix-Client": "https://chat.asozial.org",
        },
    ),
    Service(
        "XMPP-Server",
        "Das Asoziale Netzwerk hat auch einen XMPP-Server.",
        {
            "Domain": "asozial.org",
            "Software": "ejabberd",
        },
    ),
)


class ServicesHandler(HTMLRequestHandler):
    """The request handler for this page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the service list page."""
        if head:
            return
        await self.render(
            "pages/services.html",
            services=SERVICES,
        )
