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
from typing import Any

from tornado.web import HTTPError

from ..quotes import get_authors, get_quotes, get_wrong_quotes
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
        try:
            output = io.StringIO()
            source = self.request.body
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
                response: dict[str, Any] = {"success": False, "result": exc}
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
                    response = {
                        "success": True,
                        "result": eval(  # pylint: disable=eval-used
                            code, session
                        ),
                    }
                    if code.co_flags.bit_length() >= 8 and int(
                        bin(code.co_flags)[-8]
                    ):
                        response["result"] = await response["result"]
                except Exception as exc:  # pylint: disable=broad-except
                    response = {"success": False, "result": exc}
                else:
                    if response["result"] is session["help"]:
                        response["result"] = help
                    if response["result"] is session["print"]:
                        response["result"] = print
            response["result"] = (
                None
                if response["success"]
                else str()
                .join(traceback.format_exception(response["result"]))
                .strip(),
                response["result"]
                if response["success"]
                else response["result"][:2],
            )
            try:
                response["result"] = (
                    response["result"][0] or repr(response["result"][1]),
                    pickle.dumps(
                        response["result"][1], max(pickle.DEFAULT_PROTOCOL, 5)
                    ),
                )
            except (pickle.PicklingError, TypeError, RecursionError):
                response["result"] = (
                    response["result"][0] or repr(response["result"][1]),
                    None,
                )
            # except Exception as exc:
            #     response["result"] = (
            #         response["result"][0] or repr(response["result"][1]),
            #         str().join(traceback.format_exception(exc)).strip(),
            #     )
            response["output"] = (
                output.getvalue() if not output.closed else None
            )
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
            self.set_header("Content-Type", "application/vnd.python.pickle")
            await self.finish(
                pickle.dumps(exc, max(pickle.DEFAULT_PROTOCOL, 5))
            )
            return
        self.set_header("Content-Type", "application/vnd.python.pickle")
        await self.finish(
            pickle.dumps(response, max(pickle.DEFAULT_PROTOCOL, 5))
        )

    def get_default_session(self) -> dict[str, Any]:
        """Create the default session and return it."""
        return {
            "__builtins__": __builtins__,
            "__name__": "this",
            "app": self.application,
            "settings": self.settings,
            "get_wrong_quotes": get_wrong_quotes,
            "get_authors": get_authors,
            "get_quotes": get_quotes,
        }

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Respond with error message."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        if "exc_info" in kwargs:
            exc_info: tuple[
                type[BaseException], BaseException, Any  # Any ≙ traceback
            ] = kwargs[
                "exc_info"
            ]  # type: ignore
            if not issubclass(exc_info[0], HTTPError):
                self.finish(pickle.dumps(self.get_error_message(**kwargs)))
