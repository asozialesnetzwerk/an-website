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

import base64
import io
import logging
import pydoc
import traceback
from ast import PyCF_ALLOW_TOP_LEVEL_AWAIT, PyCF_ONLY_AST, PyCF_TYPE_COMMENTS
from asyncio import Future
from inspect import CO_COROUTINE  # pylint: disable=no-name-in-module
from types import TracebackType
from typing import Any

import dill as pickle  # type: ignore
import elasticapm  # type: ignore
from tornado.web import HTTPError

from .. import EVENT_REDIS, EVENT_SHUTDOWN
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permissions

logger = logging.getLogger(__name__)

PICKLE_PROTOCOL = max(pickle.DEFAULT_PROTOCOL, 5)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/backdoor/(eval|exec)", Backdoor),),
        name="Backdoor",
        description="🚪",
        aliases=("/api/hintertür", "/api/hintertuer"),
        hidden=True,
    )


class PrintWrapper:  # pylint: disable=too-few-public-methods
    """Wrapper for print()."""

    def __init__(self, output: io.TextIOBase) -> None:  # noqa: D107
        self._output: io.TextIOBase = output

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        if "file" not in kwargs:
            kwargs["file"] = self._output
        print(*args, **kwargs)


class Backdoor(APIRequestHandler):
    """The Tornado request handler for the backdoor API."""

    POSSIBLE_CONTENT_TYPES: tuple[str, ...] = ("application/vnd.python.pickle",)

    ALLOWED_METHODS: tuple[str, ...] = ("POST",)
    REQUIRED_PERMISSION: Permissions = Permissions.BACKDOOR
    SUPPORTS_COOKIE_AUTHORIZATION: bool = False

    sessions: dict[str, dict[str, Any]] = {}

    async def post(self, mode: str) -> None:  # noqa: C901
        # pylint: disable=too-complex, too-many-branches, too-many-statements
        """Handle the POST request to the backdoor API."""
        source, output = self.request.body, io.StringIO()
        exception: None | Exception = None
        output_str: None | str
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
                    result: Any = eval(  # pylint: disable=eval-used
                        code, session
                    )
                    if code.co_flags & CO_COROUTINE:
                        result = await result
                except KeyboardInterrupt:
                    EVENT_SHUTDOWN.set()
                    raise SystemExit("Shutdown initiated.") from None
            except SystemExit as exc:
                new_args = []
                for arg in exc.args:
                    try:
                        pickle.dumps(arg, PICKLE_PROTOCOL)
                    except Exception:  # pylint: disable=broad-except
                        new_args.append(repr(arg))
                    else:
                        new_args.append(arg)
                exc.args = tuple(new_args)
                output_str = output.getvalue() if not output.closed else None
                output.close()
                return await self.finish_pickled_dict(
                    success=..., output=output_str, result=exc
                )
            except Exception as exc:  # pylint: disable=broad-except
                exception = exc  # pylint: disable=redefined-variable-type
                try:
                    del result
                except UnboundLocalError:
                    pass
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
                session["self"] = None
                session["app"] = None
                session["settings"] = None
                await self.backup_session()
        output_str = output.getvalue() if not output.closed else None
        output.close()
        result_tuple: tuple[None | str, Any] = (
            "".join(traceback.format_exception(exception)).strip()
            if exception is not None
            else None,
            exception or result,
        )
        try:
            result_tuple = (
                result_tuple[0] or repr(result_tuple[1]),
                pickle.dumps(result_tuple[1], PICKLE_PROTOCOL),
            )
        except Exception:  # pylint: disable=broad-except
            result_tuple = (
                result_tuple[0] or repr(result_tuple[1]),
                None,
            )
        return await self.finish_pickled_dict(
            success=exception is None,
            output=output_str,
            result=None
            if exception is None and result is None
            else result_tuple,
        )

    def finish_pickled_dict(self, **kwargs: Any) -> Future[None]:
        """Finish with a pickled dictionary."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        return self.finish(pickle.dumps(kwargs, PICKLE_PROTOCOL))

    def get_flags(self, flags: int) -> int:
        """Get compiler flags."""
        import __future__  # pylint: disable=import-outside-toplevel

        for ftr in self.request.headers.get("X-Future-Feature", "").split(","):
            if (feature := ftr.strip()) in __future__.all_feature_names:
                flags |= getattr(__future__, feature).compiler_flag

        return flags

    def update_session(self, session: dict[str, Any]) -> dict[str, Any]:
        """Add request-specific stuff to the session."""
        session.update(self=self, app=self.application, settings=self.settings)
        return session

    async def load_session(self) -> dict[str, Any]:
        """Load the backup of a session or create a new one."""
        session_id: None | str = self.request.headers.get("X-Backdoor-Session")
        if not session_id:
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
                session = pickle.loads(
                    base64.decodebytes(session_pickle.encode("utf-8"))
                )
                for key, value in session.items():
                    try:
                        session[key] = pickle.loads(value)
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.exception(exc)
                        apm: None | elasticapm.Client = self.settings.get(
                            "ELASTIC_APM_CLIENT"
                        )
                        if apm:
                            apm.capture_exception()
            else:
                session = {
                    "__builtins__": __builtins__,
                    "__name__": "this",
                }
                if self.settings.get("TESTING"):
                    session["session_id"] = session_id
            self.sessions[session_id] = session
        return self.update_session(session)

    async def backup_session(self) -> bool:
        """Backup a session using Redis and return whether it succeeded."""
        session_id: None | str = self.request.headers.get("X-Backdoor-Session")
        if not (self.redis and session_id in self.sessions):
            return False
        session: dict[str, Any] = self.sessions[session_id].copy()
        session["self"] = None
        session["app"] = None
        session["settings"] = None
        for key, value in tuple(session.items()):
            try:
                session[key] = pickle.dumps(value, PICKLE_PROTOCOL)
            except Exception:  # pylint: disable=broad-except
                del session[key]
        return bool(
            await self.redis.setex(
                f"{self.redis_prefix}:backdoor-session:{session_id}",
                60 * 60 * 24 * 7,  # time to live in seconds (1 week)
                base64.encodebytes(pickle.dumps(session, PICKLE_PROTOCOL)),
            )
        )

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Respond with error message."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        if "exc_info" in kwargs:
            exc_info: tuple[
                type[BaseException], BaseException, TracebackType
            ] = kwargs["exc_info"]
            if not issubclass(exc_info[0], HTTPError):
                self.finish(
                    pickle.dumps(
                        self.get_error_message(**kwargs), PICKLE_PROTOCOL
                    )
                )
                return
        self.finish(pickle.dumps(None, PICKLE_PROTOCOL))
