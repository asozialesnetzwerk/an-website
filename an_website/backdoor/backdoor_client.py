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
import os
import pickle
import sys
import traceback
import uuid
from typing import Optional

from tornado.httpclient import HTTPClient, HTTPClientError

AUTH_KEY = "hunter2"
URL = "http://localhost:8080/api/backdoor/"
HTTP_CLIENT = HTTPClient()


def run(
    code: str,
    session: Optional[str] = None,
    url: str = URL,
    auth_key: str = AUTH_KEY,
):
    """Make a request to the backdoor API."""
    try:
        _c = ast.parse(code, str(), "eval")
    except SyntaxError:
        _c = ast.parse(code, str(), "exec")
    headers = {"Authorization": auth_key}
    if session:
        headers["X-REPL-Session"] = session
    try:
        response = HTTP_CLIENT.fetch(
            f"{url}/api/backdoor/",
            method="POST",
            headers=headers,
            body=pickle.dumps(_c, 5),
            validate_cert=False,
        )
    except HTTPClientError as exc:
        if exc.response and exc.response.body:
            body = pickle.loads(exc.response.body)
            exc.response._body = (  # pylint: disable=protected-access
                body if body else ...  # type: ignore
            )
        raise
    return pickle.loads(response.body)


def run_and_print(  # noqa: C901
    code: str,
    session: Optional[str] = None,
    url: str = URL,
    auth_key: str = AUTH_KEY,
):  # pylint: disable=too-many-branches
    """Run the code and print the output."""
    try:
        response = run(code, session, url, auth_key)
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
    if response is ...:
        return
    if isinstance(response, str):
        print("\033[91m" + response + "\033[0m")
        return
    if isinstance(response, SystemExit):
        raise response
    if isinstance(response, dict):
        if response["success"]:
            if response["output"]:
                print("Output:")
                print(response["output"].strip())
            if not response["result"][0] == "None":
                print("Result:")
                print(response["result"][0])
        else:
            print(response["result"][0])
    else:
        print("Response has unknown type!")
        print(response)


def startup():  # noqa: C901
    """Parse arguments, load the cache and start the backdoor client."""
    url = None
    auth_key = None
    session = None
    session_pickle = os.path.join(os.path.dirname(__file__), "session.pickle")
    if "--clear-cache" in sys.argv:
        if os.path.exists(session_pickle):
            os.remove(session_pickle)
        print("Cache cleared")
    if "--no-cache" not in sys.argv:
        try:
            with open(session_pickle, "rb") as _f:
                url, auth_key, session = pickle.load(_f)
                if "--new-session" in sys.argv:
                    print(f"Using url {url}")
                else:
                    print(f"Using url {url} with existing session {session}")
        except FileNotFoundError:
            pass
    while not url:
        url = input("URL: ").strip().rstrip("/")
        if not url:
            print("No URL given!")

    while not auth_key:
        auth_key = input("Auth key: ").strip()
        if not auth_key:
            print("No auth key given!")

    if not session or "--new-session" in sys.argv:
        session = str(uuid.uuid4())
        print(f"Creating new session {session}")

    if "--no-cache" not in sys.argv:
        with open(session_pickle, "wb") as _f:
            pickle.dump((url, auth_key, session), _f)
        print("Saved session to cache")

    # pylint: disable=import-outside-toplevel
    from pyrepl.python_reader import ReaderConsole, main  # type: ignore

    # patch the reader console to use our run function
    ReaderConsole.session = session
    ReaderConsole.execute = lambda self, code: run_and_print(
        code, self.session, url, auth_key
    )
    # run the reader
    main()


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            """Accepted arguments:
    - "--no-cache" to start without a cache
    - "--clear-cache" to clear the whole cache
    - "--new-session" to start a new session with cached url and auth key
    - "--help" to show this help message"""
        )
        sys.exit(0)
    startup()
