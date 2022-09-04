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

"""The uptime page that shows the time the website is running."""

from __future__ import annotations

import math
import time
from typing import TypedDict

import regex
from elasticsearch import AsyncElasticsearch
from tornado.web import HTTPError, RedirectHandler

from .. import EPOCH, EVENT_ELASTICSEARCH, NAME, START_TIME_NS
from ..utils.base_request_handler import BaseRequestHandler
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


class AvailabilityDict(TypedDict):  # noqa: D101
    # pylint: disable=missing-class-docstring
    up: int
    down: int
    total: int
    percentage: None | float


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/betriebszeit", UptimeHandler),
            (r"/betriebszeit/verfuegbarkeit.svg", AvailabilityChartHandler),
            (r"/api/betriebszeit", UptimeAPIHandler),
            (r"/api/uptime/*", RedirectHandler, {"url": "/api/betriebszeit"}),
        ),
        name="Betriebszeit",
        description="Die Dauer, die die Webseite am Stück in Betrieb ist",
        path="/betriebszeit",
        aliases=("/uptime",),
        keywords=("Uptime", "Betriebszeit", "Zeit"),
    )


def calculate_uptime() -> float:
    """Calculate the uptime in seconds and return it."""
    return (time.monotonic_ns() - START_TIME_NS) / 1_000_000_000


def uptime_to_str(uptime: None | float = None) -> str:
    """Convert the uptime into a string with second precision."""
    if uptime is None:
        uptime = calculate_uptime()

    # to second precision
    uptime = int(uptime)
    # divide by 60
    div_60 = int(uptime / 60)
    div_60_60 = int(div_60 / 60)

    return (
        f"{int(div_60_60 / 24)}d "
        f"{div_60_60 % 24}h "
        f"{div_60 % 60}min "
        f"{uptime % 60}s"
    )


async def get_availability_data(
    elasticsearch: AsyncElasticsearch,
) -> tuple[int, int]:  # (up, down)
    """Get the availability data."""
    data = await elasticsearch.search(
        index="heartbeat-*,synthetics-*",
        query={
            "bool": {
                "filter": [
                    {"range": {"@timestamp": {"gte": "now-1M"}}},
                    {"term": {"monitor.type": {"value": "http"}}},
                    {
                        "term": {
                            "service.name": {"value": NAME.removesuffix("-dev")}
                        }
                    },
                ]
            }
        },
        size=0,
        aggs={
            "up": {"sum": {"field": "summary.up"}},
            "down": {"sum": {"field": "summary.down"}},
        },
    )
    data.setdefault("aggregations", {"up": {"value": 0}, "down": {"value": 0}})
    return (
        int(data["aggregations"]["up"]["value"]),
        int(data["aggregations"]["down"]["value"]),
    )


def get_availability_dict(up: int, down: int) -> AvailabilityDict:
    """Get the availability data as a dict."""
    # pylint: disable=invalid-name
    return {
        "up": up,
        "down": down,
        "total": up + down,
        "percentage": 100 * up / (up + down) if up + down else None,
    }


AVAILABILITY_CHART = regex.sub(
    r"\s+",
    " ",
    """
<svg height="20"
     width="20"
     viewBox="0 0 20 20"
     xmlns="http://www.w3.org/2000/svg"
><circle r="10" cx="10" cy="10" fill="red" />
    <circle r="5" cx="10" cy="10" fill="transparent"
        stroke="green"
        stroke-width="10"
        stroke-dasharray="%2.2f 31.4159"
        transform="rotate(-90) translate(-20)" />
</svg>
""".strip(),
)


class UptimeHandler(HTMLRequestHandler):
    """The request handler for the uptime page."""

    COMPUTE_ETAG = False

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        self.set_header("Cache-Control", "no-cache")
        if head:
            return
        availability_data = (
            await get_availability_data(self.elasticsearch)
            if EVENT_ELASTICSEARCH.is_set()
            else (0, 0)
        )
        availability = get_availability_dict(*availability_data)["percentage"]
        await self.render(
            "pages/uptime.html",
            uptime=(uptime := calculate_uptime()),
            uptime_str=uptime_to_str(uptime),
            availability=availability,
        )


class AvailabilityChartHandler(BaseRequestHandler):
    """The request handler for the availability chart."""

    POSSIBLE_CONTENT_TYPES = ("image/svg+xml",)
    COMPUTE_ETAG = False

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        if not (availability := self.get_argument("a", None)):
            if not EVENT_ELASTICSEARCH.is_set():
                raise HTTPError(503)
            availability_data = await get_availability_data(self.elasticsearch)
            self.redirect(
                self.fix_url(
                    self.request.full_url(),
                    a=int(
                        (
                            get_availability_dict(*availability_data)[
                                "percentage"
                            ]
                            or 0
                        )
                        * 100
                    )
                    / (100 * 100),
                ),
                permanent=False,
            )
            return
        self.set_header(
            "Cache-Control", f"public, min-fresh={60 * 60 * 24 * 14}, immutable"
        )
        if head:
            return
        await self.finish(
            AVAILABILITY_CHART % (math.pi * 10 * float(availability))
        )


class UptimeAPIHandler(APIRequestHandler):
    """The request handler for the uptime API."""

    COMPUTE_ETAG = False

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests."""
        self.set_header("Cache-Control", "no-cache")
        if head:
            return
        availability_data = (
            await get_availability_data(self.elasticsearch)
            if EVENT_ELASTICSEARCH.is_set()
            else (0, 0)
        )
        return await self.finish_dict(
            uptime=(uptime := calculate_uptime()),
            uptime_str=uptime_to_str(uptime),
            start_time=time.time() - uptime - EPOCH,
            availability=get_availability_dict(*availability_data),
        )
