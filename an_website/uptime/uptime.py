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

import time
from collections import Counter
from typing import Literal

from elasticsearch import AsyncElasticsearch

from ..__main__ import NAME
from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo

START_TIME = time.monotonic()


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/uptime/", UptimeHandler),
            (r"/api/uptime/", UptimeAPIHandler),
        ),
        name="Betriebszeit",
        description="Die Dauer die die Webseite am Stück in Betrieb ist",
        path="/uptime/",
        keywords=("uptime", "Betriebszeit", "Zeit"),
    )


def calculate_uptime() -> float:
    """Calculate the uptime in seconds and return it."""
    return time.monotonic() - START_TIME


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


async def get_uptime_perc(
    elasticsearch: AsyncElasticsearch, hours: Literal[1, 6, 12, 24]
) -> str:
    """Get the uptime percentage for the last `hours`."""
    up_perc_counter: Counter[str] = Counter(
        [
            hit["_source"]["monitor"]["status"]  # "up" / "down"
            for hit in (
                await elasticsearch.search(
                    index="heartbeat*",
                    query={
                        "bool": {
                            "must": [
                                {
                                    "range": {
                                        "@timestamp": {
                                            "gte": f"now-{hours}h",
                                        },
                                    },
                                },
                                {
                                    "term": {
                                        "monitor.id": {
                                            "value": NAME,
                                        }
                                    },
                                },
                            ]
                        }
                    },
                    size=10_000,
                    _source=[
                        "monitor.id",
                        "monitor.status",
                        # "@timestamp"  # TODO: Cache with the timestamp
                    ],
                )
            )["hits"]["hits"]
            # if hit["_source"]["monitor"]["id"] == NAME
        ]
    )
    _up, down = up_perc_counter["up"], up_perc_counter["down"]
    total = _up + down
    perc = 100 * _up / total if total else 0
    return f"{_up}/{total} ({perc}%)"


class UptimeHandler(BaseRequestHandler):
    """The request handler for the uptime page."""

    async def get(self) -> None:
        """Handle the GET request and render the page."""
        await self.render(
            "pages/uptime.html",
            uptime=(uptime := calculate_uptime()),
            uptime_str=uptime_to_str(uptime),
        )


class UptimeAPIHandler(APIRequestHandler):
    """The request handler for the uptime API."""

    async def get(self) -> None:
        """Handle the GET request to the API."""
        return await self.finish(
            {
                "uptime": (uptime := calculate_uptime()),
                "uptime_str": uptime_to_str(uptime),
                "start_time": time.time() - uptime,
                # "uptime_perc_last_24h": await get_uptime_perc(
                #     self.elasticsearch, 24
                # ),
                # "uptime_perc_last_12h": await get_uptime_perc(
                #     self.elasticsearch, 12
                # ),
                "uptime_perc_last_1h": await get_uptime_perc(
                    self.elasticsearch, 1
                )
                if self.elasticsearch
                else "n/a",
            }
        )
