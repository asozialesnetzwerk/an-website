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
import sys
import traceback
from asyncio import AbstractEventLoop
from collections.abc import Awaitable, Callable
from concurrent.futures import Future
from datetime import datetime, tzinfo
from logging import LogRecord
from typing import Any

import orjson as json


class AsyncHandler(logging.Handler):
    """A logging handler that can handle log records asynchronously."""

    future_references: dict[Future[Any], LogRecord]
    emitter: Callable[[str], Awaitable[Any] | None]
    callback: Callable[[Future[Any]], None]
    loop: AbstractEventLoop

    def __init__(
        self,
        level: int | str = logging.NOTSET,
        *,
        emitter: Callable[[str], Awaitable[Any] | None],
        callback: Callable[[Future[Any]], None] = lambda _: None,
        loop: AbstractEventLoop,
    ):
        """Initialize the handler."""
        super().__init__(level=level)
        self.future_references = {}
        self.emitter = emitter  # type: ignore[assignment, misc]
        self.callback = callback  # type: ignore[assignment, misc]
        self.loop = loop

    def _callback(self, future: Future[Any]) -> None:
        self.acquire()
        try:
            if exc := future.exception():
                record = self.future_references[future]
                self.handle_error(record, exc)
            self.future_references.pop(future)
        finally:
            self.release()
        self.callback(future)  # type: ignore[call-arg, misc]

    def emit(self, record: LogRecord) -> None:
        """Handle incoming log records."""
        try:
            if self.loop.is_closed():
                return
            message = self.format(record)
            awaitable = self.emitter(message)  # type: ignore[call-arg, misc]
            if awaitable:
                future = asyncio.run_coroutine_threadsafe(awaitable, self.loop)
                self.future_references[future] = record
                future.add_done_callback(self._callback)
        except Exception as exc:  # pylint: disable=broad-except
            self.handle_error(record, exc)

    def handle_error(self, record: LogRecord, exception: BaseException) -> None:
        """Handle errors which occur during an emit() call or in the future."""
        # pylint: disable=no-self-use, too-many-try-statements, while-used
        if logging.raiseExceptions and sys.stderr:
            try:
                sys.stderr.write("--- Logging error ---\n")
                traceback.print_exception(exception)
                frame = (
                    exception.__traceback__.tb_frame
                    if exception.__traceback__
                    else None
                )
                while frame and frame.f_code.co_filename == __file__:
                    frame = frame.f_back
                while frame and frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                if frame:
                    sys.stderr.write("Call stack:\n")
                    traceback.print_stack(frame)
                else:
                    sys.stderr.write(
                        f"Logged from file {record.filename}, line {record.lineno}\n"
                    )
                try:
                    sys.stderr.write(
                        f"Message: {record.msg!r}\nArguments: {record.args}\n"
                    )
                except RecursionError:
                    raise
                except Exception:  # pylint: disable=broad-except
                    sys.stderr.write(
                        "Unable to print the message and arguments"
                        " - possible formatting error.\nUse the"
                        " traceback above to help find the error.\n"
                    )
            except OSError:
                pass
            finally:
                del frame


class WebhookFormatter(logging.Formatter):
    """A logging formatter optimized for logging to a webhook."""

    timezone: None | tzinfo = None
    escape_message = False

    def format(self, record: LogRecord) -> str:
        """Format the specified record as text."""
        record.message = record.getMessage()
        if self.escape_message:
            record.message = json.dumps(record.message).decode("ascii")[1:-1]
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        return self.formatMessage(record)

    def formatTime(  # noqa: N802
        self, record: LogRecord, datefmt: None | str = None
    ) -> str:
        """Return the creation time of the specified LogRecord as formatted text."""
        spam = datetime.fromtimestamp(record.created).astimezone(self.timezone)
        if datefmt:
            return spam.strftime(datefmt)
        return spam.isoformat()
