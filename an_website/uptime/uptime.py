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

import asyncio
import logging
import time
from collections import Counter
from collections.abc import Awaitable
from typing import Any, Literal

import tornado.web
from aioredis import Redis
from elasticsearch import AsyncElasticsearch

from ..__main__ import NAME  # pylint: disable=cyclic-import
from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo

START_TIME = time.monotonic()


logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/uptime/", UptimeHandler),
            (r"/api/uptime/", UptimeAPIHandler),
        ),
        name="Betriebszeit",
        description="Die Dauer die, die Webseite am Stück in Betrieb ist",
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


async def get_uptime_perc_periodically(
    app: tornado.web.Application,  # pylint: disable=duplicate-code
    setup_redis_awaitable: None | Awaitable[Any] = None,
    setup_es_awaitable: None | Awaitable[Any] = None,
) -> None:
    """Get the uptime percentage periodically."""
    if setup_redis_awaitable:
        await setup_redis_awaitable
    if setup_es_awaitable:
        await setup_es_awaitable
    redis: None | Redis = app.settings.get("REDIS")
    prefix: None | str = app.settings.get("REDIS_PREFIX", str())
    elasticsearch: None | AsyncElasticsearch = app.settings.get(
        "ELASTICSEARCH"
    )
    if not redis or not elasticsearch:
        logger.warning(
            "Redis or Elasticsearch not available. "
            "Don't get uptime periodically."
        )
        return
    # pylint: disable=while-used
    while True:
        hours: tuple[Literal[1, 12, 24], ...] = (1, 12, 24)
        for _h in hours:
            await get_uptime_perc(
                elasticsearch=elasticsearch,
                hours=_h,
                redis=redis,
                redis_prefix=prefix,
                get_from_cache=False,
            )
        logger.debug("Got uptime percentage.")
        await asyncio.sleep(5 * 60)  # every 5 minutes


async def get_uptime_perc(
    elasticsearch: AsyncElasticsearch,
    hours: Literal[1, 12, 24],
    redis: None | Redis = None,
    redis_prefix: None | str = None,
    get_from_cache: bool = True,
) -> tuple[int, int]:  # (up, down)
    """Get the uptime percentage for the last `hours`."""
    if (
        get_from_cache
        and redis
        and (val := await redis.get(f"{redis_prefix}:uptime:last_{hours}h"))
    ):
        # get the uptime from redis
        upp, down = val.split(",")
    else:
        up_perc_counter: Counter[str] = Counter(
            [
                hit["_source"]["monitor"]["status"]  # is "up" or "down"
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
                        size=10_000,  # max size (is more than needed for 24h)
                        _source=[
                            "monitor.id",
                            "monitor.status",
                        ],
                    )
                )["hits"]["hits"]
            ]
        )
        upp, down = up_perc_counter["up"], up_perc_counter["down"]
        if redis:
            await redis.setex(
                f"{redis_prefix}:uptime:last_{hours}h",
                5 * 60 + 10,  # 5 minutes (+ 10 seconds (for safety))
                f"{upp},{down}",
            )
    return int(upp), int(down)


def get_up_perc_dict(upp: int, down: int) -> dict[str, int | float]:
    """Get the uptime percentage as a dict."""
    return {
        "up": upp,
        "down": down,
        "total": upp + down,
        "perc": 100 * upp / (upp + down) if upp + down else 0,
    }


class UptimeHandler(BaseRequestHandler):
    """The request handler for the uptime page."""

    async def get(self) -> None:
        """Handle the GET request and render the page."""
        self.set_header("Cache-Control", "no-cache")
        await self.render(
            "pages/uptime.html",
            uptime=(uptime := calculate_uptime()),
            uptime_str=uptime_to_str(uptime),
        )


class UptimeAPIHandler(APIRequestHandler):
    """The request handler for the uptime API."""

    async def get(self) -> None:
        """Handle the GET request to the API."""
        self.set_header("Cache-Control", "no-cache")
        return await self.finish(
            {
                "uptime": (uptime := calculate_uptime()),
                "uptime_str": uptime_to_str(uptime),
                "start_time": time.time() - uptime,
                "perc_last_24h": get_up_perc_dict(
                    *(
                        await get_uptime_perc(
                            self.elasticsearch,
                            24,
                            self.redis,
                            self.redis_prefix,
                        )
                    )
                )
                if self.elasticsearch and self.redis  # would take too long
                else None,
                "perc_last_12h": get_up_perc_dict(
                    *(
                        await get_uptime_perc(
                            self.elasticsearch,
                            12,
                            self.redis,
                            self.redis_prefix,
                        )
                    )
                )
                if self.elasticsearch and self.redis  # would take too long
                else None,
                "perc_last_1h": get_up_perc_dict(
                    *(
                        await get_uptime_perc(
                            self.elasticsearch,
                            1,
                            self.redis,
                            self.redis_prefix,
                        )
                    )
                )
                if self.elasticsearch
                else None,
            }
        )
