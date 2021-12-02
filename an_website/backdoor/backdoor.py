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
        handlers=(
            (r"/api/backdoor/", Backdoor),
            (r"/api/backdoor/(eval|exec)/", Backdoor),
        ),
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

    async def post(self, mode=None):  # noqa: C901
        # pylint: disable=too-many-branches, too-many-statements
        """Handle the POST request to the backdoor API."""
        try:
            output = io.StringIO()
            if mode:
                source = self.request.body
            else:
                try:
                    source = pickle.loads(self.request.body)
                except Exception:  # pylint: disable=broad-except
                    raise HTTPError(400)  # pylint: disable=raise-missing-from
                if isinstance(source, ast.Expression):
                    mode = "eval"
                elif isinstance(source, ast.Module):
                    mode = "exec"
                else:
                    raise HTTPError(400)
            try:
                try:
                    code = compile(
                        source,
                        str(),
                        mode,
                        __future__.barry_as_FLUFL.compiler_flag,
                        0x5F3759DF,
                    )
                    top_level_await = False
                except SyntaxError:
                    code = compile(
                        source,
                        str(),
                        mode,
                        __future__.barry_as_FLUFL.compiler_flag
                        | ast.PyCF_ALLOW_TOP_LEVEL_AWAIT,
                        0x5F3759DF,
                    )
                    top_level_await = True
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
                        "result": eval(  # pylint: disable=eval-used
                            code, globals_dict
                        ),
                    }
                    if top_level_await:
                        response["result"] = await response["result"]
                except Exception:  # pylint: disable=broad-except
                    response = {"success": False, "result": sys.exc_info()}
            response["result"] = (
                None
                if response["success"]
                else str()
                .join(traceback.format_exception(*response["result"]))
                .strip(),
                response["result"]
                if response["success"]
                else response["result"][:2],
            )
            try:
                response["result"] = (
                    response["result"][0] or repr(response["result"][1]),
                    pickle.dumps(response["result"][1], 5),
                )
            except (pickle.PicklingError, TypeError, RecursionError):
                response["result"] = (
                    response["result"][0] or repr(response["result"][1]),
                    None,
                )
            # except Exception:  # pylint: disable=broad-except
            #     response["result"] = (
            #         response["result"][0] or repr(response["result"][1]),
            #         str().join(traceback.format_exception(*sys.exc_info())).strip(),
            #     )
            response["output"] = (
                output.getvalue() if not output.closed else None
            )
        except HTTPError:
            raise
        except Exception:  # pylint: disable=broad-except
            self.set_status(500)
            response = (
                str().join(traceback.format_exception(*sys.exc_info())).strip()
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
            response = exc
        self.set_header("Content-Type", "application/vnd.python.pickle")
        await self.finish(
            pickle.dumps(response, max(pickle.DEFAULT_PROTOCOL, 5))
        )

    def write_error(self, status_code, **kwargs):
        """Respond with None in case of error."""
        self.set_header("Content-Type", "application/vnd.python.pickle")
        self.finish(pickle.dumps(None))
