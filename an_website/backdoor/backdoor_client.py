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
from typing import Optional

from tornado.httpclient import HTTPClient, HTTPClientError

AUTH_KEY = "hunter2"
API_URL = "http://localhost:8080/api/backdoor/"
HTTP_CLIENT = HTTPClient()


def run(code: str, session: Optional[str] = None):
    """Make a request to the backdoor API."""
    try:
        _c = ast.parse(code, str(), "eval")
    except SyntaxError:
        _c = ast.parse(code, str(), "exec")
    headers = {"Authorization": AUTH_KEY}
    if session:
        headers["X-REPL-Session"] = session
    try:
        response = HTTP_CLIENT.fetch(
            API_URL,
            method="POST",
            headers=headers,
            body=pickle.dumps(_c, 5),
            validate_cert=False,
        )
    except HTTPClientError as exc:
        if exc.response and exc.response.body:
            exc.response._body = (  # pylint: disable=protected-access
                pickle.loads(exc.response.body)
            )
        raise
    return pickle.loads(response.body)


def run_and_print(code: str, session: Optional[str] = None):
    """Run the code and print the output."""
    try:
        response = run(code, session)
    except SyntaxError:
        print(
            str()
            .join(traceback.format_exception_only(*sys.exc_info()[0:2]))
            .strip()
        )
        return
    except HTTPClientError as exc:
        print("\033[91m" + str(exc) + "\033[0m")
        if exc.response and exc.response.body:
            response = exc.response.body
        else:
            return
    if isinstance(response, str):
        print("\033[91m" + response + "\033[0m")
        return
    if isinstance(response, SystemExit):
        raise response
    if response["success"]:
        if response["output"]:
            print("Output:")
            print(response["output"].strip())
        if not response["result"][0] == "None":
            print("Result:")
            print(response["result"][0])
    else:
        print(response["result"][0])


if __name__ == "__main__":
    from pyrepl.python_reader import ReaderConsole, main  # type: ignore

    # patch the reader console to use our run function
    ReaderConsole.session = str(uuid.uuid4())
    ReaderConsole.execute = lambda self, code: run_and_print(
        code, self.session
    )
    # run the reader
    main()
