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

"""The client for the backdoor api of the website."""
from __future__ import annotations

import ast
import os
import pickle
import re

from tornado.httpclient import HTTPClient

AUTH_KEY = "hunter2"
API_URL = "http://localhost:8080/api/backdoor/"
HTTP_CLIENT = HTTPClient()


def run(code: str, session: str = os.urandom(32).hex()):
    """Make a request to the backdoor api."""
    _c = ast.parse(code, "input.py", "exec")
    result = HTTP_CLIENT.fetch(
        API_URL,
        method="POST",
        body=pickle.dumps(_c, 5),
        headers={
            "Authorization": AUTH_KEY,
            "X-REPL-Session": session,
        },
        raise_error=False,
    )
    return pickle.loads(result.body)


def main():  # noqa: C901
    """Run the client."""
    while True:
        try:
            code = input(">>> ")
        except EOFError:
            break
        try:
            if "\n" not in code and not code.startswith("print"):
                code = f"print({code})"
                # replace assignment with walrus
                code = re.sub(
                    r"([^=])=([^=])", lambda _m: f"{_m[1]}:={_m[2]}", code
                )
            result = run(code)
        except Exception as _e:  # pylint: disable=broad-except
            print(_e)
            continue
        if result["success"]:
            if isinstance(result["result"][1], bytes):
                _r = pickle.loads(result["result"][1])
                if _r is not None:
                    print(_r)
            else:
                print(result["result"][1])
            if result["output"]:
                print(result["output"])
        else:
            if isinstance(result["result"][0], list):
                print("\033[91m" + ("".join(result["result"][0])) + "\033[0m")
            else:
                print("\033[91m" + result["result"][0] + "\033[0m")


if __name__ == "__main__":
    main()
