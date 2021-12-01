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

"""The client for the backdoor API of the website."""
from __future__ import annotations

import ast
import pickle
import sys
import traceback
import uuid

from tornado.httpclient import HTTPClient

AUTH_KEY = "hunter2"
API_URL = "http://localhost:8080/api/backdoor/"
HTTP_CLIENT = HTTPClient()


def run(code: str, session: str = str(uuid.uuid4())):
    """Make a request to the backdoor API."""
    try:
        _c = ast.parse(code, str(), "eval")
    except SyntaxError:
        _c = ast.parse(code, str(), "exec")
    response = HTTP_CLIENT.fetch(
        API_URL,
        raise_error=False,
        method="POST",
        headers={
            "Authorization": AUTH_KEY,
            "X-REPL-Session": session,
        },
        body=pickle.dumps(_c, 5),
        validate_cert=False,
    )
    return pickle.loads(response.body)


def main():  # noqa: C901  # pylint: disable=too-many-branches
    """Run the client."""
    while True:
        try:
            code = input(">>> ").strip()
        except EOFError:
            break
        if code.endswith(":"):
            while _c := input("... ").rstrip():
                code += "\n" + _c
        if not code:
            continue
        try:
            response = run(code)
        except SyntaxError:
            print(
                str().join(
                    traceback.format_exception_only(*sys.exc_info()[0:2])
                )
            )
            continue
        if response["success"]:
            if response["output"]:
                print("Output:")
                print(response["output"])
            if not response["result"][0] == "None":
                print("Result:")
                print(response["result"][0])
                print()
        else:
            print("\033[91m" + response["result"][0] + "\033[0m")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
