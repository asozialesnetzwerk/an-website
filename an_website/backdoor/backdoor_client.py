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

import hy  # type: ignore
from tornado.httpclient import HTTPClient, HTTPClientError

HTTP_CLIENT = HTTPClient()


def run(
    url: str,
    key: str,
    code: str,
    session: Optional[str] = None,
    use_hy: bool = False,
):
    """Make a request to the backdoor API."""
    if use_hy:
        code = hy.disassemble(hy.read_str(code), True)
    try:
        _c = ast.parse(code, str(), "eval")
    except SyntaxError:
        _c = ast.parse(code, str(), "exec")
    headers = {"Authorization": key}
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
            exc.response._body = (  # pylint: disable=protected-access
                pickle.loads(exc.response.body) or ...  # type: ignore
            )
        raise
    return pickle.loads(response.body)


def run_and_print(  # noqa: C901
    url: str,
    key: str,
    code: str,
    session: Optional[str] = None,
    use_hy: bool = False,
):  # pylint: disable=too-many-branches
    """Run the code and print the output."""
    try:
        response = run(url, key, code, session, use_hy)
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
    key = None
    session = None
    session_pickle = os.path.expanduser(
        "~/.cache/an-backdoor-client/session.pickle"
    )
    if "--clear-cache" in sys.argv:
        if os.path.exists(session_pickle):
            os.remove(session_pickle)
        print("Cache cleared")
    if "--no-cache" not in sys.argv:
        try:
            with open(session_pickle, "rb") as _f:
                url, key, session = pickle.load(_f)
                if "--new-session" in sys.argv:
                    print(f"Using URL {url}")
                else:
                    print(f"Using URL {url} with existing session {session}")
        except FileNotFoundError:
            pass
    while not url:
        url = input("URL: ").strip().rstrip("/")
        if not url:
            print("No URL given!")

    while not key:
        key = input("Key: ").strip()
        if not key:
            print("No key given!")

    if not session or "--new-session" in sys.argv:
        session = str(uuid.uuid4())
        print(f"Creating new session {session}")

    if "--no-cache" not in sys.argv:
        os.makedirs(os.path.dirname(session_pickle), exist_ok=True)
        with open(session_pickle, "wb") as _f:
            pickle.dump((url, key, session), _f)
        print("Saved session to cache")

    # pylint: disable=import-outside-toplevel
    from pyrepl.python_reader import ReaderConsole, main  # type: ignore

    # patch the reader console to use our run function
    ReaderConsole.execute = lambda self, code: run_and_print(
        url, key, code, session, "--use-hy" in sys.argv
    )
    # run the reader
    main()


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            """Accepted arguments:
    - "--no-cache" to start without a cache
    - "--clear-cache" to clear the whole cache
    - "--new-session" to start a new session with cached URL and key
    - "--help" to show this help message
    - "--use-hy" to use hy instead of python"""
        )
        sys.exit(0)
    startup()
