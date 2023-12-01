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

"""The backdoor API of the website."""

from __future__ import annotations

import io
import logging
import pickle  # nosec: B403
import pickletools  # nosec: B403
import pydoc
import traceback
from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT, PyCF_ONLY_AST, PyCF_TYPE_COMMENTS
from asyncio import Future
from base64 import b85decode, b85encode
from collections.abc import MutableMapping
from inspect import CO_COROUTINE  # pylint: disable=no-name-in-module
from types import TracebackType
from typing import Any, ClassVar, Final, cast

import dill  # type: ignore[import]  # nosec: B403
import jsonpickle  # type: ignore[import]
from tornado.web import HTTPError

from .. import EVENT_REDIS, EVENT_SHUTDOWN, pytest_is_running
from ..utils.decorators import requires
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import Permission

LOGGER: Final = logging.getLogger(__name__)


class PrintWrapper:  # pylint: disable=too-few-public-methods
    """Wrapper for print()."""

    def __call__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D102
        kwargs.setdefault("file", self._output)
        print(*args, **kwargs)

    def __init__(self, output: io.TextIOBase) -> None:  # noqa: D107
        self._output: io.TextIOBase = output


class Backdoor(APIRequestHandler):
    """The request handler for the backdoor API."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "application/vnd.uqfoundation.dill",
        "application/vnd.python.pickle",
        "application/json",
        "text/plain",
    )

    ALLOWED_METHODS: ClassVar[tuple[str, ...]] = ("POST",)

    sessions: ClassVar[dict[str, dict[str, Any]]] = {}

    async def backup_session(self) -> bool:
        """Backup a session using Redis and return whether it succeeded."""
        session_id: None | str = self.request.headers.get("X-Backdoor-Session")
        if not (EVENT_REDIS.is_set() and session_id in self.sessions):
            return False
        session: dict[str, Any] = self.sessions[session_id].copy()
        session.pop("self", None)
        session.pop("app", None)
        session.pop("settings", None)
        for key, value in tuple(session.items()):
            try:
                session[key] = pickletools.optimize(
                    dill.dumps(value, max(dill.DEFAULT_PROTOCOL, 5))
                )
            except Exception:  # pylint: disable=broad-except
                del session[key]
        return bool(
            await self.redis.setex(
                f"{self.redis_prefix}:backdoor-session:{session_id}",
                60 * 60 * 24 * 7,  # time to live in seconds (1 week)
                b85encode(pickletools.optimize(dill.dumps(session))),
            )
        )

    def finish_serialized_dict(self, **kwargs: Any) -> Future[None]:
        """Finish with a serialized dictionary."""
        return self.finish(self.serialize(kwargs))

    def get_flags(self, flags: int) -> int:
        """Get compiler flags."""
        import __future__  # pylint: disable=import-outside-toplevel

        for ftr in self.request.headers.get("X-Future-Feature", "").split(","):
            if (feature := ftr.strip()) in __future__.all_feature_names:
                flags |= getattr(__future__, feature).compiler_flag

        return flags

    def get_protocol_version(self) -> int:
        """Get the protocol version for the response."""
        try:  # pylint: disable=line-too-long
            return min(
                int(
                    self.request.headers.get("X-Pickle-Protocol"), base=0  # type: ignore[arg-type]  # noqa: B950
                ),
                pickle.HIGHEST_PROTOCOL,
            )
        except (TypeError, ValueError):
            return 5

    async def load_session(self) -> dict[str, Any]:
        """Load the backup of a session or create a new one."""
        if not (session_id := self.request.headers.get("X-Backdoor-Session")):
            session: dict[str, Any] = {
                "__builtins__": __builtins__,
                "__name__": "this",
            }
        elif session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            session_pickle = (
                await self.redis.get(
                    f"{self.redis_prefix}:backdoor-session:{session_id}"
                )
                if EVENT_REDIS.is_set()
                else None
            )
            if session_pickle:
                session = dill.loads(b85decode(session_pickle))  # nosec: B301
                for key, value in session.items():
                    try:
                        session[key] = dill.loads(value)  # nosec: B301
                    except Exception:  # pylint: disable=broad-except
                        LOGGER.exception("Loading the session failed")
                        if self.apm_client:
                            self.apm_client.capture_exception()
            else:
                session = {
                    "__builtins__": __builtins__,
                    "__name__": "this",
                }
                if pytest_is_running():
                    session["session_id"] = session_id
            self.sessions[session_id] = session
        self.update_session(session)
        return session

    @requires(Permission.BACKDOOR, allow_cookie_auth=False)
    async def post(self, mode: str) -> None:  # noqa: C901
        # pylint: disable=too-complex, too-many-branches
        # pylint: disable=too-many-locals, too-many-statements
        """Handle POST requests to the backdoor API."""
        source, output = self.request.body, io.StringIO()
        exception: None | Exception = None
        output_str: None | str
        result: Any
        try:
            parsed = compile(
                source,
                "",
                mode,
                self.get_flags(PyCF_ONLY_AST | PyCF_TYPE_COMMENTS),
                0x5F3759DF,
                _feature_version=10,
            )
            code = compile(
                parsed,
                "",
                mode,
                self.get_flags(PyCF_ALLOW_TOP_LEVEL_AWAIT),
                0x5F3759DF,
                _feature_version=10,
            )
        except SyntaxError as exc:
            exception = exc
            result = exc
        else:
            session = await self.load_session()
            if "print" not in session or isinstance(
                session["print"], PrintWrapper
            ):
                session["print"] = PrintWrapper(output)
            if "help" not in session or isinstance(
                session["help"], pydoc.Helper
            ):
                session["help"] = pydoc.Helper(io.StringIO(), output)
            try:
                try:
                    result = eval(  # pylint: disable=eval-used  # nosec: B307
                        code, session
                    )
                    if code.co_flags & CO_COROUTINE:
                        result = await result
                except KeyboardInterrupt:
                    EVENT_SHUTDOWN.set()
                    raise SystemExit("Shutdown initiated.") from None
            except SystemExit as exc:  # TODO: FIX BUG
                new_args = []
                for arg in exc.args:
                    try:
                        self.serialize(arg)
                    except Exception:  # pylint: disable=broad-except
                        new_args.append(repr(arg))
                    else:
                        new_args.append(arg)
                exc.args = tuple(new_args)
                output_str = output.getvalue() if not output.closed else None
                output.close()
                return await self.finish_serialized_dict(
                    success=..., output=output_str, result=exc
                )
            except Exception as exc:  # pylint: disable=broad-except
                exception = exc  # pylint: disable=redefined-variable-type
                result = exc
            else:
                if result is not None:  # noqa: F821
                    if result is session.get(  # noqa: F821
                        "print"
                    ) and isinstance(
                        result, PrintWrapper  # noqa: F821
                    ):
                        result = print
                    elif result is session.get("help") and isinstance(
                        session["help"], pydoc.Helper
                    ):
                        result = help
                    session["_"] = result
            finally:
                session.pop("self", None)
                session.pop("app", None)
                session.pop("settings", None)
                await self.backup_session()
        output_str = output.getvalue() if not output.closed else None
        output.close()
        exception_text = (
            "".join(traceback.format_exception(exception)).strip()
            if exception is not None
            else None
        )
        if self.content_type == "text/plain":
            if mode == "exec":
                return await self.finish(exception_text or output_str)
            return await self.finish(exception_text or repr(result))
        try:
            serialized_result: None | bytes = self.serialize(result)
        except Exception:  # pylint: disable=broad-except
            serialized_result = None
        result_tuple: tuple[None | str, None | bytes] = (
            exception_text or repr(result),
            serialized_result,
        )
        return await self.finish_serialized_dict(
            success=exception is None,
            output=output_str,
            result=None
            if exception is None and result is None
            else result_tuple,
        )

    def serialize(self, data: Any, protocol: None | int = None) -> bytes:
        """Serialize the data and return it."""
        if self.content_type == "application/json":
            return cast(bytes, jsonpickle.encode(data))
        protocol = protocol or self.get_protocol_version()
        if self.content_type == "application/vnd.uqfoundation.dill":
            return cast(bytes, dill.dumps(data, protocol))
        return pickle.dumps(data, protocol)

    def update_session(self, session: MutableMapping[str, Any]) -> None:
        """Add request-specific stuff to the session."""
        session.update(self=self, app=self.application, settings=self.settings)

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Respond with error message."""
        if self.content_type not in {
            "application/vnd.python.pickle",
            "application/vnd.uqfoundation.dill",
        }:
            super().write_error(status_code, **kwargs)
            return
        if "exc_info" in kwargs:
            exc_info: tuple[
                type[BaseException], BaseException, TracebackType
            ] = kwargs["exc_info"]
            if not issubclass(exc_info[0], HTTPError):
                self.finish(self.serialize(self.get_error_message(**kwargs)))
                return
        self.finish(self.serialize((status_code, self._reason)))
