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

"""Logging stuff used by the website."""

from __future__ import annotations

import asyncio
import logging
import os
from asyncio import AbstractEventLoop
from collections.abc import Awaitable
from concurrent.futures import Future
from datetime import datetime, tzinfo
from logging import LogRecord
from typing import Any, cast

import orjson as json
from tornado.httpclient import AsyncHTTPClient

from .. import DIR as ROOT_DIR


class AsyncHandler(logging.Handler):
    """A logging handler that can handle log records asynchronously."""

    futures: set[Future[Any]]
    loop: AbstractEventLoop

    def __init__(
        self,
        level: int | str = logging.NOTSET,
        *,
        loop: AbstractEventLoop,
    ):
        """Initialize the handler."""
        super().__init__(level=level)
        self.futures = set()
        self.loop = loop

    def callback(self, future: Future[Any]) -> None:
        """Remove the reference to the future from the handler."""
        self.acquire()
        try:
            self.futures.discard(future)
        finally:
            self.release()

    def emit(  # type: ignore[override]
        self, record: LogRecord
    ) -> None | Awaitable[Any]:
        """
        Do whatever it takes to actually log the specified logging record.

        This version is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError(
            "emit must be implemented by AsyncHandler subclasses"
        )

    def handle(  # type: ignore[override]
        self, record: LogRecord
    ) -> bool | LogRecord:
        """Handle incoming log records."""
        rv = cast(  # pylint: disable=invalid-name
            bool | LogRecord, self.filter(record)
        )
        if isinstance(rv, LogRecord):
            record = rv
        if rv and not self.loop.is_closed():
            self.acquire()
            try:
                if awaitable := self.emit(record):
                    future = asyncio.run_coroutine_threadsafe(
                        awaitable, self.loop
                    )
                    self.futures.add(future)
                    future.add_done_callback(self.callback)
            finally:
                self.release()
        return rv


class DatetimeFormatter(logging.Formatter):
    """A logging formatter that formats the time using datetime."""

    timezone: None | tzinfo = None

    def formatTime(  # noqa: N802
        self, record: LogRecord, datefmt: None | str = None
    ) -> str:
        """Return the creation time of the LogRecord as formatted text."""
        spam = datetime.fromtimestamp(record.created).astimezone(self.timezone)
        if datefmt:
            return spam.strftime(datefmt)
        return spam.isoformat()


class WebhookFormatter(DatetimeFormatter):
    """A logging formatter optimized for logging to a webhook."""

    escape_message = False

    def format(self, record: LogRecord) -> str:
        """Format the specified record as text."""
        record.message = record.getMessage()
        if self.escape_message:
            record.message = json.dumps(record.message).decode("UTF-8")[1:-1]
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        return self.formatMessage(record)


class WebhookHandler(AsyncHandler):
    """A logging handler that sends logs to a webhook."""

    url: str
    content_type: str

    def __init__(
        self,
        level: int | str = logging.NOTSET,
        *,
        loop: AbstractEventLoop,
        url: str,
        content_type: str,
    ):
        """Initialize the handler."""
        super().__init__(level=level, loop=loop)
        self.url = url
        self.content_type = content_type

    async def emit(self, record: LogRecord) -> None:  # type: ignore[override]
        """Send the request to the webhook."""
        # pylint: disable=invalid-overridden-method
        try:
            message = self.format(record)
            await AsyncHTTPClient().fetch(
                self.url,
                method="POST",
                headers={"Content-Type": self.content_type},
                body=message.strip(),
                ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
            )
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)
