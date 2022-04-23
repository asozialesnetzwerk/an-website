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

from __future__ import annotations, barry_as_FLUFL

import ast
import base64
import io
import logging
import pydoc
import traceback
from inspect import CO_COROUTINE  # pylint: disable=no-name-in-module
from types import TracebackType
from typing import Any

import dill as pickle  # type: ignore
import elasticapm  # type: ignore
from tornado.web import HTTPError

from ..quotes import get_authors, get_quotes, get_wrong_quote, get_wrong_quotes
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permissions

logger = logging.getLogger(__name__)


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

    def __call__(self, *args: list[Any], **kwargs: dict[str, Any]) -> None:
        if "file" not in kwargs:
            kwargs["file"] = self._output  # type: ignore
        print(*args, **kwargs)  # type: ignore


class Backdoor(APIRequestHandler):
    """The Tornado request handler for the backdoor API."""

    ALLOWED_METHODS: tuple[str, ...] = ("POST",)
    REQUIRED_PERMISSION: Permissions = Permissions.BACKDOOR
    SUPPORTS_COOKIE_AUTHORIZATION: bool = False
    PICKLE_PROTOCOL = max(pickle.DEFAULT_PROTOCOL, 5)

    sessions: dict[str, dict[str, Any]] = {}

    async def post(self, mode: str) -> None:  # noqa: C901
        # pylint: disable=too-complex, too-many-branches, too-many-statements
        """Handle the POST request to the backdoor API."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        try:
            result: Any
            exception: None | BaseException = None
            source, output = self.request.body, io.StringIO()
            try:
                parsed = compile(
                    source,
                    "",
                    mode,
                    barry_as_FLUFL.compiler_flag
                    | ast.PyCF_ONLY_AST
                    | ast.PyCF_TYPE_COMMENTS,
                    0x5F3759DF,
                    _feature_version=10,
                )
                code = compile(
                    parsed,
                    "",
                    mode,
                    barry_as_FLUFL.compiler_flag
                    | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                    0x5F3759DF,
                    _feature_version=10,
                )
            except SyntaxError as exc:
                exception = exc
            else:
                session_id: None | str = self.request.headers.get(
                    "X-Backdoor-Session"
                )
                session: dict[str, Any] = await self.load_session(session_id)
                if "print" not in session or isinstance(
                    session["print"], PrintWrapper
                ):
                    session["print"] = PrintWrapper(output)
                if "help" not in session or isinstance(
                    session["help"], pydoc.Helper
                ):
                    session["help"] = pydoc.Helper(io.StringIO(), output)

                try:
                    result = eval(code, session)  # pylint: disable=eval-used
                    if code.co_flags & CO_COROUTINE:
                        result = await result
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
                await self.save_session(session)
            output_str: None | str = (
                output.getvalue() if not output.closed else None
            )
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
                    pickle.dumps(result_tuple[1], self.PICKLE_PROTOCOL),
                )
            except Exception:  # pylint: disable=broad-except
                result_tuple = (
                    result_tuple[0] or repr(result_tuple[1]),
                    None,
                )
        except SystemExit as exc:
            new_args = []
            for arg in exc.args:
                try:
                    pickle.dumps(arg)
                except Exception:  # pylint: disable=broad-except
                    new_args.append(repr(arg))
                else:
                    new_args.append(arg)
            exc.args = tuple(new_args)
            return await self.finish(pickle.dumps(exc, self.PICKLE_PROTOCOL))
        return await self.finish(
            pickle.dumps(
                {
                    "success": exception is None,
                    "output": output_str,
                    "result": None
                    if exception is None and result is None
                    else result_tuple,
                },
                self.PICKLE_PROTOCOL,
            )
        )

    def update_session(self, session: dict[str, Any]) -> dict[str, Any]:
        """Update a session with important default values."""
        session.update(
            __builtins__=__builtins__,
            __name__="this",
            self=self,
            app=self.application,
            settings=self.settings,
            get_authors=get_authors,
            get_quotes=get_quotes,
            get_wq=get_wrong_quote,
            get_wqs=get_wrong_quotes,
        )
        return session

    async def load_session(self, session_id: None | str) -> dict[str, Any]:
        """Load the backup of a session or create a new one."""
        if not session_id:
            session: dict[str, Any] = {}
        elif session_id in self.sessions:
            session = self.sessions[session_id]
        else:
            session = {}
            if self.redis:
                session_pickle = await self.redis.get(
                    f"{self.redis_prefix}:backdoor-session:{session_id}"
                )
                if session_pickle:
                    try:
                        session = pickle.loads(
                            base64.decodebytes(session_pickle.encode("utf-8"))
                        )
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.exception(exc)
                        apm: None | elasticapm.Client = self.settings.get(
                            "ELASTIC_APM_CLIENT"
                        )
                        if apm:
                            apm.capture_exception()
            # save the session as session_id is truthy
            self.sessions[session_id] = session
        if session_id:
            session["session_id"] = session_id
        return self.update_session(session)

    async def save_session(self, session: dict[str, Any]) -> bool:
        """Backup a session using Redis and return whether it succeeded."""
        if not self.redis or "session_id" not in session:
            return False
        session_id = session["session_id"]
        if self.sessions.get(session_id) is not session:
            return False
        try:
            # delete stuff that gets set in update_session
            # this avoids errors and reduces the pickle size
            for var in (
                "__builtins__",
                "self",
                "app",
                "settings",
                "get_authors",
                "get_quotes",
                "get_wq",
                "get_wqs",
            ):
                del session[var]
            session_pickle = pickle.dumps(session, self.PICKLE_PROTOCOL)
        except Exception as exc:  # pylint: disable=broad-except
            self.update_session(session)
            logger.exception(exc)
            apm: None | elasticapm.Client = self.settings.get(
                "ELASTIC_APM_CLIENT"
            )
            if apm:
                apm.capture_exception()
            return False
        else:
            self.update_session(session)

        return bool(
            await self.redis.setex(
                f"{self.redis_prefix}:backdoor-session:{session_id}",
                60 * 60 * 24 * 7,  # time to live in seconds (1 week)
                base64.encodebytes(
                    session_pickle
                ),  # value to save (the session)
            )
        )

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Respond with error message."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        if "exc_info" in kwargs:
            exc_info: tuple[
                type[BaseException], BaseException, TracebackType
            ] = kwargs[
                "exc_info"
            ]  # type: ignore
            if not issubclass(exc_info[0], HTTPError):
                self.finish(
                    pickle.dumps(
                        self.get_error_message(**kwargs), self.PICKLE_PROTOCOL
                    )
                )
                return None
        self.finish(pickle.dumps(None, self.PICKLE_PROTOCOL))
        return None
