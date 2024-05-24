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
"""Tasks running in the background."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable, Iterable, Sequence
from functools import wraps
from typing import TYPE_CHECKING, Final, Protocol, assert_type, cast

import typed_stream
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis
from tornado.web import Application

from .. import EVENT_ELASTICSEARCH, EVENT_REDIS, EVENT_SHUTDOWN
from .elasticsearch_setup import setup_elasticsearch_configs

if TYPE_CHECKING:
    from .utils import ModuleInfo

LOGGER: Final = logging.getLogger(__name__)

HEARTBEAT: float = 0
PEAK_FUNC: Final[Callable[[BackgroundTask], object]] = (
    typed_stream.functions.noop
)


class BackgroundTask(Protocol):
    """A protocol representing a background task."""

    async def __call__(self, *, app: Application, worker: int | None) -> None:
        """Start the background task."""

    @property
    def __name__(self) -> str:  # pylint: disable=bad-dunder-name
        """The name of the task."""


async def check_elasticsearch(
    app: Application, worker: int | None
) -> None:  # pragma: no cover
    """Check Elasticsearch."""
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        es: AsyncElasticsearch = cast(
            AsyncElasticsearch, app.settings.get("ELASTICSEARCH")
        )
        try:
            await es.transport.perform_request("HEAD", "/")
        except Exception:  # pylint: disable=broad-except
            EVENT_ELASTICSEARCH.clear()
            LOGGER.exception(
                "Connecting to Elasticsearch failed on worker: %s", worker
            )
        else:
            if not EVENT_ELASTICSEARCH.is_set():
                try:
                    await setup_elasticsearch_configs(
                        es, app.settings["ELASTICSEARCH_PREFIX"]
                    )
                except Exception:  # pylint: disable=broad-except
                    LOGGER.exception(
                        "An exception occured while configuring Elasticsearch on worker: %s",  # noqa: B950
                        worker,
                    )
                else:
                    EVENT_ELASTICSEARCH.set()
        await asyncio.sleep(20)


async def check_if_ppid_changed(ppid: int) -> None:
    """Check whether Technoblade hates us."""
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        if os.getppid() != ppid:
            EVENT_SHUTDOWN.set()
            return
        await asyncio.sleep(1)


async def check_redis(
    app: Application, worker: int | None
) -> None:  # pragma: no cover
    """Check Redis."""
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        redis: Redis[str] = cast("Redis[str]", app.settings.get("REDIS"))
        try:
            await redis.ping()
        except Exception:  # pylint: disable=broad-except
            EVENT_REDIS.clear()
            LOGGER.exception("Connecting to Redis failed on worker %s", worker)
        else:
            EVENT_REDIS.set()
        await asyncio.sleep(20)


async def heartbeat() -> None:
    """Heartbeat."""
    global HEARTBEAT  # pylint: disable=global-statement
    while HEARTBEAT:  # pylint: disable=while-used
        HEARTBEAT = time.monotonic()
        await asyncio.sleep(0.05)


async def wait_for_shutdown() -> None:  # pragma: no cover
    """Wait for the shutdown event."""
    loop = asyncio.get_running_loop()
    while not EVENT_SHUTDOWN.is_set():  # pylint: disable=while-used
        await asyncio.sleep(0.05)
    loop.stop()


def start_background_tasks(  # pylint: disable=too-many-arguments
    *,
    app: Application,
    processes: int,
    module_infos: Iterable[ModuleInfo],
    loop: asyncio.AbstractEventLoop,
    main_pid: int,
    elasticsearch_is_enabled: bool,
    redis_is_enabled: bool,
    worker: int | None,
) -> Sequence[asyncio.Task[object]]:
    """Start all required background tasks."""
    return assert_type(
        typed_stream.Stream(module_infos)
        .flat_map(lambda info: info.required_background_tasks)
        .chain(
            typed_stream.Stream((heartbeat, wait_for_shutdown)).map(
                lambda fun: wraps(fun)(lambda **_: fun())
            )
        )
        .chain(
            [
                wraps(check_if_ppid_changed)(
                    lambda **k: check_if_ppid_changed(main_pid)
                )
            ]
            if processes
            else ()
        )
        .chain([check_elasticsearch] if elasticsearch_is_enabled else ())
        .chain([check_redis] if redis_is_enabled else ())
        .distinct()
        .peek(
            PEAK_FUNC
            if worker
            else lambda fun: LOGGER.info(
                "starting %s.%s background service",
                fun.__module__,
                fun.__name__,
            )
        )
        .map(lambda fun: fun(app=app, worker=worker))
        .map(loop.create_task)
        .collect(tuple),
        tuple[asyncio.Task[None], ...],
    )
