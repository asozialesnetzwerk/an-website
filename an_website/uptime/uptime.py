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
from collections.abc import Awaitable
from typing import Any

import elasticapm  # type: ignore
import tornado.web
from aioredis import Redis
from elasticsearch import AsyncElasticsearch

from .. import NAME
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
        description="Die Dauer, die die Webseite am Stück in Betrieb ist",
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


async def update_availability_data_periodically(
    app: tornado.web.Application,
    setup_redis_awaitable: None | Awaitable[Any] = None,
    setup_es_awaitable: None | Awaitable[Any] = None,
) -> None:
    """Update the availability data periodically."""
    if setup_redis_awaitable:
        await setup_redis_awaitable
    if setup_es_awaitable:
        await setup_es_awaitable
    # pylint: disable=while-used
    while True:
        await update_availability_data(app)
        await asyncio.sleep(5)


async def update_availability_data(app: tornado.web.Application) -> None:
    """Update the availability data."""
    redis: None | Redis = app.settings.get("REDIS")
    redis_prefix: str = app.settings.get("REDIS_PREFIX", "")
    elasticsearch: None | AsyncElasticsearch = app.settings.get(
        "ELASTICSEARCH"
    )

    if not (redis and elasticsearch):
        return

    logger.info("Updating availability data...")
    try:
        data = await elasticsearch.search(
            index="heartbeat-*,synthetics-*",
            query={
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "now-1M",
                                },
                            },
                        },
                        {
                            "term": {
                                "service.name": {
                                    "value": NAME,
                                }
                            },
                        },
                        {
                            "term": {
                                "monitor.type": {
                                    "value": "http",
                                }
                            },
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
        # pylint: disable=invalid-name
        up, down = (
            int(data["aggregations"]["up"]["value"]),
            int(data["aggregations"]["down"]["value"]),
        )
        await redis.setex(
            f"{redis_prefix}:availability",
            30,  # TTL
            f"{up}|{down}",
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception(exc)
        logger.error("Updating availability data failed.")
        apm: None | elasticapm.Client = app.settings.get("ELASTIC_APM_CLIENT")
        if apm:
            apm.capture_exception()
    else:
        logger.info("Updated availability data successfully.")


async def get_availability_data(
    redis: Redis, redis_prefix: str
) -> None | tuple[int, int]:  # (up, down)
    """Get the availability data."""
    data = await redis.get(f"{redis_prefix}:availability")
    if not data:
        return None
    # pylint: disable=invalid-name
    up, down = data.split("|")
    return int(up), int(down)


def get_availability_dict(up: int, down: int) -> dict[str, int | float]:
    # pylint: disable=invalid-name
    """Get the availability data as a dict."""
    return {
        "up": up,
        "down": down,
        "total": up + down,
        "percentage": 100 * up / (up + down) if up + down else 0,
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
        availability_data = (
            await get_availability_data(
                self.redis,
                self.redis_prefix,
            )
            if self.elasticsearch and self.redis
            else None
        )
        return await self.finish(
            {
                "uptime": (uptime := calculate_uptime()),
                "uptime_str": uptime_to_str(uptime),
                "start_time": time.time() - uptime,
                "availability": get_availability_dict(*availability_data)
                if availability_data
                else None,
            }
        )
