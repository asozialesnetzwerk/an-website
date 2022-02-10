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
from __future__ import annotations, barry_as_FLUFL

import ast
import asyncio
import http.client
import os
import pickle
import pydoc
import re
import sys
import traceback
import urllib.parse
import uuid
from typing import Any

try:
    import hy  # type: ignore
except ImportError:
    hy = None


S = lambda *A: re.match(*A, 24).groups()  # type: ignore[call-overload]  # noqa: E731


async def request(m, u, h, b):  # type: ignore[no-untyped-def]  # noqa: D103
    # pylint: disable=invalid-name, line-too-long, missing-function-docstring, too-many-locals, while-used
    s, _, a, _, q, _ = z = urllib.parse.urlparse(u)
    t, e, d, n = s != b"http", ..., b"", z.hostname
    r, w = await asyncio.open_connection(
        n, int(z.port or 80 + 363 * t), ssl=t, server_hostname=[None, n][t]
    )
    w.write(
        m
        + b" "
        + (a or b"/")
        + [b"?" + q, b""][q == b""]
        + b" HTTP/1.0"
        + b"\r\n"
        + b"\r\n".join([b"%b:%b" % w for w in h] + [b"", b])
    )
    await w.drain()
    while c := await r.read():
        if b"\r\n\r\n" in (d := d + c) * (e is ...):
            e, d = d.split(b"\r\n\r\n", 1)  # type: ignore[assignment]
            t, o = S(rb"HTTP/.+? (\d+).*?%b(.*)" % b"\r\n", e)  # type: ignore[no-untyped-call]
            o = [S(rb"([^\s]+):\s*(.+?)\s*$", x) for x in o.split(b"\r\n")]  # type: ignore[no-untyped-call]
    w.close()
    return int(t), o, d


def detect_mode(code: str) -> str:
    """Detect which mode needs to be used."""
    try:
        ast.parse(code, mode="eval")
        return "eval"
    except SyntaxError:
        ast.parse(code, mode="exec")
        return "exec"


def send(
    url: str,
    key: str,
    code: str,
    mode: str = "exec",
    session: None | str = None,
) -> Any:
    """Send code to the backdoor API."""
    parsed_url = urllib.parse.urlparse(url)
    body = code.encode("utf-8")
    headers = [
        (b"Host", parsed_url.hostname.encode("latin-1")),  # type: ignore[union-attr]
        (b"Content-Length", str(len(body)).encode("latin-1")),
        (b"Authorization", key.encode("latin-1")),
    ]
    if session:
        headers.append((b"X-Backdoor-Session", session.encode("latin-1")))
    response = asyncio.run(
        request(  # type: ignore[no-untyped-call]
            b"POST",
            f"{url}/api/backdoor/{mode}/".encode("latin-1"),
            tuple(headers),
            body,
        )
    )
    return response[0], response[1], pickle.loads(response[2])


def lisp_always_active() -> bool:
    """Return True if LISP is always active."""
    return (
        hy
        and not hy.eval(
            hy.read_str(
                '(* (- (* (+ 0 1) 2 3 4 5) (+ 6 7 8 9 10 11)) '  # fmt: skip
                '(int (= (. (__import__ "os.path") sep) "/")))'
            )
        )
        and not int.from_bytes(
            getattr(
                os, "洀漀搀渀愀爀甀".encode("utf_16_be")[::-1].decode("utf_16_be")
            )(1),
            sys.byteorder,
        )
        // (69 // 4 - 1)
    )


def run_and_print(  # noqa: C901
    url: str,
    key: str,
    code: str,
    session: None | str = None,
    lisp: bool = False,
) -> None:
    # pylint: disable=too-complex, too-many-branches
    """Run the code and print the output."""
    if lisp or lisp_always_active():
        code = hy.disassemble(hy.read_str(code), True)
    try:
        response = send(url, key, code, detect_mode(code), session)
    except SyntaxError as exc:
        print(
            "".join(
                traceback.format_exception_only(exc)  # type: ignore
            ).strip()
        )
        return
    if response[0] >= 400:
        print("\033[91m" + http.client.responses[response[0]] + "\033[0m")
    if response[2] is None:
        return
    if isinstance(response[2], str):
        print("\033[91m" + response[2] + "\033[0m")
        return
    if isinstance(response[2], SystemExit):
        raise response[2]
    if isinstance(response[2], dict):
        if response[2]["success"]:
            if response[2]["output"]:
                print("Output:")
                print(response[2]["output"].strip())
            result_obj = None
            if response[2]["result"][1]:
                try:
                    result_obj = pickle.loads(response[2]["result"][1])
                except (
                    pickle.UnpicklingError,
                    AttributeError,
                    EOFError,
                    ImportError,
                    IndexError,
                ):
                    pass
                except Exception:  # pylint: disable=broad-except
                    traceback.print_exc()
            if (
                isinstance(result_obj, tuple)
                and len(result_obj) == 2
                and result_obj[0] == "HelperTuple"
                and isinstance(result_obj[1], str)
            ):
                pydoc.pager(result_obj[1])
            elif response[2]["result"][0] != "None":
                print("Result:")
                print(response[2]["result"][0])
        else:
            print(response[2]["result"][0])
    else:
        print("Response has unknown type!")
        print(response[2])


def start() -> None:  # noqa: C901
    # pylint: disable=too-complex, too-many-branches, too-many-statements
    """Parse arguments, load the cache and start the backdoor client."""
    url = None
    key = None
    session = None
    session_pickle = os.path.join(
        os.getenv("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
        "an-backdoor-client/session.pickle",
    )
    if "--clear-cache" in sys.argv:
        if os.path.exists(session_pickle):
            os.remove(session_pickle)
        print("Cache cleared")
    if "--no-cache" not in sys.argv:
        try:
            with open(session_pickle, "rb") as file:
                url, key, session = pickle.load(file)
                if "--new-session" in sys.argv:
                    print(f"Using URL {url}")
                else:
                    print(f"Using URL {url} with existing session {session}")
        except FileNotFoundError:
            pass
    while not url:  # pylint: disable=while-used
        url = input("URL: ").strip().rstrip("/")
        if not url:
            print("No URL given!")
        elif not url.startswith("http"):
            banana = url.split("/", maxsplit=1)
            if re.fullmatch(
                r"(?:localhost|127\.0\.0\.1|\[::1\])(?:\:\d+)?", banana[0]
            ):
                url = "http://" + url
            else:
                url = "https://" + url
            print(f"Using URL {url}")

    while not key:  # pylint: disable=while-used
        key = input("Key: ").strip()
        if not key:
            print("No key given!")

    if not session or "--new-session" in sys.argv:
        session = input("Session (enter nothing for random session): ")
        if not session:
            session = str(uuid.uuid4())
        print(f"Using session {session}")

    if "--no-cache" not in sys.argv:
        os.makedirs(os.path.dirname(session_pickle), exist_ok=True)
        with open(session_pickle, "wb") as file:
            pickle.dump((url, key, session), file)
        print("Saved session to cache")

    if "--no-patch-help" not in sys.argv:
        code = (
            "def help(*args, **kwargs):\n"
            "    import io\n"
            "    import pydoc\n"
            "    helper_output = io.StringIO()\n"
            "    pydoc.Helper(io.StringIO(), helper_output)(*args, **kwargs)\n"
            "    return 'HelperTuple', helper_output.getvalue()"
        )
        response = send(url, key, code, "exec", session)
        if response[0] >= 400 or not response[2]["success"]:
            print("\033[91mPatching help() failed!\033[0m")

    if "--lisp" in sys.argv:
        if not hy:
            sys.exit("Hy is not installed!")
        response = send(url, key, "import hy", "exec", session)
        if response[0] >= 400 or not response[2]["success"]:
            print("\033[91mImporting Hy failed!\033[0m")

    # pylint: disable=import-outside-toplevel
    from pyrepl.python_reader import ReaderConsole, main  # type: ignore

    # patch the reader console to use our run function
    ReaderConsole.execute = lambda self, code: run_and_print(
        url, key, code, session, "--lisp" in sys.argv
    )

    # run the reader
    main()


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(
            """Accepted arguments:
    - "--no-patch-help" to not patch help()
    - "--no-cache" to start without a cache
    - "--clear-cache" to clear the whole cache
    - "--new-session" to start a new session with cached URL and key
    - "--lisp" to enable Lots of Irritating Superfluous Parentheses
    - "--help" to show this help message"""
        )
        sys.exit()
    for arg in sys.argv[1:]:
        if arg not in (
            "--no-patch-help",
            "--no-cache",
            "--clear-cache",
            "--new-session",
            "--lisp",
            "--help",
            "-h",
        ):
            print(f"Unknown argument: {arg}")
            sys.exit(64 + 4 + 1)
    try:
        start()
    except (EOFError, KeyboardInterrupt):
        print("Exiting.")
