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

import __future__
import ast
import io
import pickle
import sys
import traceback
from typing import Dict

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/backdoor/", Backdoor),),
        name="Backdoor",
        description="🚪",
        path="/api/backdoor/",
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
    RATELIMIT_TOKENS: int = 0

    sessions: Dict[str, dict] = {}

    async def post(self):  # noqa: C901
        """Handle the POST request to the backdoor API."""
        output = io.StringIO()
        node = pickle.loads(self.request.body)
        try:
            if isinstance(node, ast.Expression):
                code = compile(
                    node,
                    str(),
                    "eval",
                    __future__.barry_as_FLUFL.compiler_flag
                    | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                    0x5F3759DF,
                )
            elif isinstance(node, ast.Module):
                code = compile(
                    node,
                    str(),
                    "exec",
                    __future__.barry_as_FLUFL.compiler_flag
                    | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                    0x5F3759DF,
                )
            else:
                raise HTTPError(400)
        except SyntaxError:
            response = {"success": False, "result": sys.exc_info()}
        else:
            session = self.request.headers.get("X-REPL-Session")
            globals_dict = self.sessions.get(session) or {
                "app": self.application
            }
            if session and session not in self.sessions:
                self.sessions[session] = globals_dict
            globals_dict["print"] = PrintWrapper(output)
            try:
                response = {
                    "success": True,
                    "result": await eval(  # pylint: disable=eval-used
                        code, globals_dict
                    ),
                }
            except:  # noqa: E722  # pylint: disable=bare-except
                response = {"success": False, "result": sys.exc_info()}
        response["output"] = output.getvalue() if not output.closed else None
        response["result"] = (
            None
            if response["success"]
            else traceback.format_exception(*response["result"]),
            response["result"]
            if response["success"]
            else response["result"][:2],
        )
        try:
            response["result"] = (
                response["result"][0] or repr(response["result"][1]),
                pickle.dumps(response["result"][1], 5),
            )
        except (pickle.PicklingError, RecursionError):
            response["result"] = (
                response["result"][0] or repr(response["result"][1]),
                None,
            )
        self.set_header("Content-Type", "application/vnd.python.pickle")
        await self.finish(pickle.dumps(response, 5))
