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
import traceback
from asyncio import AbstractEventLoop
from collections.abc import Coroutine, Iterable
from concurrent.futures import Future
from datetime import datetime, tzinfo
from logging import LogRecord
from pathlib import Path
from typing import Never

import orjson as json
from tornado.httpclient import AsyncHTTPClient

from an_website import DIR as AN_WEBSITE_DIR

from .. import CA_BUNDLE_PATH

HOME: str = Path("~/").expanduser().as_posix().rstrip("/")


def minify_filepath(path: str) -> str:
    """Make a filepath smaller."""
    if path.startswith(f"{HOME}/"):
        return "~" + path.removeprefix(HOME)
    return path


def get_minimal_traceback(
    record: LogRecord, prefix: str = "\n\n"
) -> Iterable[str]:
    """Get a minimal traceback from the log record."""
    if not record.exc_info:
        return
    (_, value, tb) = record.exc_info
    if not (value and tb):
        return

    yield prefix
    yield from traceback.format_exception(value, limit=0)

    summary = traceback.extract_tb(tb)
    if isinstance(AN_WEBSITE_DIR, Path):
        start_path = f"{str(AN_WEBSITE_DIR).rstrip('/')}/"

        for i in reversed(range(len(summary))):
            if summary[i].filename.startswith(start_path):
                summary = traceback.StackSummary(summary[i:])
                break

    for frame in summary:
        frame.filename = minify_filepath(frame.filename)

    yield from summary.format()


class AsyncHandler(logging.Handler):
    """A logging handler that can handle log records asynchronously."""

    futures: set[Future[object]]
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

    def callback(self, future: Future[object]) -> None:
        """Remove the reference to the future from the handler."""
        self.acquire()
        try:
            self.futures.discard(future)
        finally:
            self.release()

    def emit(  # type: ignore[override]
        self, record: LogRecord
    ) -> None | Coroutine[None, Never, object]:
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
        rv = self.filter(record)
        if isinstance(rv, LogRecord):
            record = rv
        if rv and not self.loop.is_closed():
            self.acquire()
            try:
                if awaitable := self.emit(record):
                    future: Future[object] = asyncio.run_coroutine_threadsafe(
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
    max_message_length: int | None = None

    def format(self, record: LogRecord) -> str:
        """Format the specified record as text."""
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        if (
            self.max_message_length is not None
            and len(record.message) > self.max_message_length
        ):
            record.message = record.message[: self.max_message_length]
        for line in get_minimal_traceback(record):
            if (
                self.max_message_length is not None
                and len(line) + len(record.message) > self.max_message_length
            ):
                if len("...") + len(record.message) <= self.max_message_length:
                    record.message += "..."
                break
            record.message += line
        if self.escape_message:
            record.message = json.dumps(record.message).decode("UTF-8")[1:-1]
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
                ca_certs=CA_BUNDLE_PATH,
            )
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)
