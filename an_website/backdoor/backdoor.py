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

from ..quotes import get_wrong_quotes
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

    def __init__(self, output):  # noqa: D107
        self._output = output

    def __call__(self, *args, **kwargs):
        if "file" not in kwargs:
            kwargs["file"] = self._output
        print(*args, **kwargs)


class Backdoor(APIRequestHandler):
    """The Tornado request handler for the backdoor API."""

    ALLOWED_METHODS: tuple[str, ...] = ("POST",)
    REQUIRES_AUTHORIZATION: bool = True

    sessions: dict[str, dict] = {}

    async def post(self, mode):  # noqa: C901
        # pylint: disable=too-many-branches
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
                response = {"success": False, "result": exc}
            else:
                session_id = self.request.headers.get("X-Backdoor-Session")
                session: dict[str, Any] = self.sessions.get(session_id) or {
                    "__builtins__": __builtins__,
                    "__name__": "this",
                    "app": self.application,
                    "get_wrong_quotes": get_wrong_quotes,
                }
                if session_id and session_id not in self.sessions:
                    self.sessions[session_id] = session
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
                exc.code = repr(exc.code)
            new_args = []
            for arg in exc.args:
                try:
                    pickle.dumps(arg)
                    new_args.append(arg)
                except Exception:  # pylint: disable=broad-except
                    new_args.append(repr(arg))
            exc.args = tuple(new_args)
            response = exc  # pylint: disable=redefined-variable-type
        self.set_header("Content-Type", "application/vnd.python.pickle")
        await self.finish(
            pickle.dumps(response, max(pickle.DEFAULT_PROTOCOL, 5))
        )

    def write_error(self, status_code, **kwargs):
        """Respond with error message."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            self.finish(pickle.dumps(self.get_error_message(**kwargs)))
