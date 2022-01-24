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
import io
import pickle
import pydoc
import traceback
from types import TracebackType
from typing import Any

from tornado.web import HTTPError

from ..quotes import get_authors, get_quotes, get_wrong_quote, get_wrong_quotes
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/backdoor/(eval|exec)/", Backdoor),),
        name="Backdoor",
        description="🚪",
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
    REQUIRES_AUTHORIZATION: bool = True

    sessions: dict[str, dict[str, Any]] = {}

    async def post(  # noqa: C901  # pylint: disable=too-many-statements, too-many-branches
        self, mode: str
    ) -> None:
        """Handle the POST request to the backdoor API."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        try:
            exception: None | BaseException = None
            result: Any = None
            source, output = self.request.body, io.StringIO()
            try:
                parsed = compile(
                    source,
                    str(),
                    mode,
                    barry_as_FLUFL.compiler_flag
                    | ast.PyCF_ONLY_AST
                    | ast.PyCF_TYPE_COMMENTS,
                    0x5F3759DF,
                    _feature_version=10,
                )
                code = compile(
                    parsed,
                    str(),
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
                if session_id:
                    session: dict[str, Any] = (
                        self.sessions.get(session_id)
                        or self.get_default_session()
                    )
                    if session_id not in self.sessions:
                        self.sessions[session_id] = session
                else:
                    session = self.get_default_session()

                if "print" not in session or isinstance(
                    session["print"], PrintWrapper
                ):
                    session["print"] = PrintWrapper(output)
                if "help" not in session or isinstance(
                    session["help"], pydoc.Helper
                ):
                    session["help"] = pydoc.Helper(io.StringIO(), output)
                try:
                    _result = eval(code, session)  # pylint: disable=eval-used
                    result = (
                        await _result
                        if code.co_flags.bit_length() >= 8
                        and int(bin(code.co_flags)[-8])
                        else _result
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    exception = exc  # pylint: disable=redefined-variable-type
                else:
                    if result is session["help"]:
                        result = help
                    elif result is session["print"]:
                        result = print
                    if result is not None:
                        session["_"] = result
            result_tuple: tuple[None | str, Any] = (
                str()
                .join(traceback.format_exception(exception))  # type: ignore
                .strip()
                if exception
                else None,
                exception or result,
            )
            try:
                result_tuple = (
                    result_tuple[0] or repr(result_tuple[1]),
                    pickle.dumps(
                        result_tuple[1], max(pickle.DEFAULT_PROTOCOL, 5)
                    ),
                )
            except (pickle.PicklingError, TypeError, RecursionError):
                result_tuple = (
                    result_tuple[0] or repr(result_tuple[1]),
                    None,
                )
            # except Exception as exc:
            #     response["result"] = (
            #         response["result"][0] or repr(response["result"][1]),
            #         str().join(traceback.format_exception(exc)).strip(),
            #     )
        except SystemExit as exc:
            if not isinstance(exc.code, int):
                exc.code = repr(exc.code)  # type: ignore
            new_args = []
            for arg in exc.args:
                try:
                    pickle.dumps(arg)
                    new_args.append(arg)
                except Exception:  # pylint: disable=broad-except
                    new_args.append(repr(arg))
            exc.args = tuple(new_args)
            return await self.finish(
                pickle.dumps(exc, max(pickle.DEFAULT_PROTOCOL, 5))
            )
        return await self.finish(
            pickle.dumps(
                {
                    "success": not exception,
                    "result": result_tuple,
                    "output": output.getvalue() if not output.closed else None,
                },
                max(pickle.DEFAULT_PROTOCOL, 5),
            )
        )

    def get_default_session(self) -> dict[str, Any]:
        """Create the default session and return it."""
        return {
            "__builtins__": __builtins__,
            "__name__": "this",
            "app": self.application,
            "settings": self.settings,
            "redis": self.redis,
            "redis_prefix": self.redis_prefix,
            "elasticsearch": self.elasticsearch,
            "elasticsearch_prefix": self.elasticsearch_prefix,
            "get_wq": get_wrong_quote,
            "get_wqs": get_wrong_quotes,
            "get_authors": get_authors,
            "get_quotes": get_quotes,
        }

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
                self.finish(pickle.dumps(self.get_error_message(**kwargs)))
                return None
        self.finish(pickle.dumps(None))
        return None
