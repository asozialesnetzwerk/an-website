#!/usr/bin/env python3

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
import asyncio
import contextlib
import http.client
import io
import os
import pickle  # nosec: B403
import pydoc
import re  # pylint: disable=preferred-module
import socket
import sys
import time
import traceback
import uuid
from base64 import b64encode
from collections.abc import Callable, Iterable
from types import EllipsisType
from typing import Any, TypedDict
from urllib.parse import SplitResult, quote, quote_plus, urlsplit

with contextlib.suppress(ImportError):
    import dill as pickle  # type: ignore[import, no-redef]  # noqa: F811  # nosec: B403

try:
    import hy  # type: ignore[import]
except ImportError:
    hy = None

try:
    import idna
except ImportError:
    idna = None  # type: ignore[assignment]

try:
    import socks  # type: ignore[import]
except ImportError:
    socks = None

try:
    import uvloop
except ImportError:
    pass
else:
    uvloop.install()


FLUFL = True

E = eval(  # pylint: disable=eval-used  # nosec: B307
    "eval(repr((_:=[],_.append(_))[0]))[0][0]"
)


class Response(TypedDict):  # noqa: D101
    # pylint: disable=missing-class-docstring
    success: bool | EllipsisType
    output: None | str
    result: None | tuple[str, None | bytes] | SystemExit


async def create_socket(  # noqa: C901  # pylint: disable=too-many-arguments
    addr: str,
    port: int | str,
    proxy_type: None | int = None,
    proxy_addr: None | str = None,
    proxy_port: None | int = None,
    proxy_rdns: None | bool = True,
    proxy_username: None | str = None,
    proxy_password: None | str = None,
) -> socket.socket | socks.socksocket:
    """Create a socket (optionally with a proxy)."""
    # pylint: disable=too-complex
    if proxy_type is not None and proxy_addr is None:
        raise TypeError(
            "proxy_addr should not be None if proxy_type is not None"
        )
    if proxy_type is not None and proxy_rdns is None:
        raise TypeError(
            "proxy_rdns should not be None if proxy_type is not None"
        )
    if proxy_type is not None and not socks:
        raise NotImplementedError("PySocks is required for proxy support")
    loop = asyncio.get_running_loop()
    address_infos = await loop.getaddrinfo(
        addr,
        port,
        # PySocks doesn't support AF_INET6
        family=0 if proxy_type is None else socket.AF_INET,
        type=socket.SOCK_STREAM,
    )
    if not address_infos:
        raise OSError("getaddrinfo() returned empty list")
    exceptions = []
    for address_info in address_infos:
        sock = None
        try:
            sock = (
                socks.socksocket(
                    address_info[0], address_info[1], address_info[2]
                )
                if proxy_type is not None
                else socket.socket(
                    address_info[0], address_info[1], address_info[2]
                )
            )
            sock.setblocking(False)
            if proxy_type is not None:
                sock.set_proxy(
                    proxy_type,
                    proxy_addr,
                    proxy_port,
                    proxy_rdns,
                    proxy_username,
                    proxy_password,
                )
            await loop.sock_connect(sock, address_info[4])
            return sock
        except OSError as exc:
            if sock is not None:
                sock.close()
            exceptions.append(exc)
            continue
        except BaseException:
            if sock is not None:
                sock.close()
            raise
    if len(exceptions) == 1:
        raise exceptions[0]
    model = str(exceptions[0])
    if all(str(exc) == model for exc in exceptions):
        raise exceptions[0]
    raise OSError(
        f"Multiple exceptions: {', '.join(str(exc) for exc in exceptions)}"
    )


async def request(  # noqa: C901  # pylint: disable=too-many-branches, too-many-locals
    method: str,
    url: str | SplitResult,
    headers: None | dict[str, str] = None,
    body: None | bytes | Iterable[bytes] | str = None,
    *,
    proxy_type: None | int = None,
    proxy_addr: None | str = None,
    proxy_port: None | int = None,
    proxy_rdns: None | bool = True,
    proxy_username: None | str = None,
    proxy_password: None | str = None,
) -> tuple[int, dict[str, str], bytes]:
    """Insanely awesome HTTP client."""
    # pylint: disable=invalid-name, line-too-long, too-complex, while-used
    if isinstance(url, str):
        url = urlsplit(url)
    if url.scheme not in {"", "http", "https"}:
        raise ValueError(f"Unsupported scheme: {url.scheme}")
    if not url.hostname:
        raise ValueError("URL has no hostname")
    if headers is None:
        headers = {}
    if isinstance(body, str):
        body = body.encode("UTF-8")
    if isinstance(body, memoryview):
        body = body.tobytes()  # type: ignore[unreachable]
    if isinstance(body, Iterable) and not isinstance(body, (bytes, bytearray)):
        body = b"".join(body)  # type: ignore[arg-type]
    https = url.scheme == "https"
    header_names = [x.strip().title() for x in headers.keys()]
    if "Host" not in header_names:
        host: None | str = None
        if idna:
            with contextlib.suppress(idna.core.InvalidCodepoint):
                host = idna.encode(url.hostname).decode("ASCII")
                host = f"{host}:{url.port}" if url.port else host
        if not host:
            host = url.netloc.encode("IDNA").decode("ASCII")
        headers["Host"] = host
    if body and "Content-Length" not in header_names:
        headers["Content-Length"] = str(len(body))
    e, data = E, b""
    sock = await create_socket(
        url.hostname,
        url.port or ("https" if https else "http"),
        proxy_type,
        proxy_addr,
        proxy_port,
        proxy_rdns,
        proxy_username,
        proxy_password,
    )
    reader, writer = await asyncio.open_connection(
        sock=sock,
        ssl=https,
        server_hostname=url.hostname if https else None,
    )
    writer.write(
        (
            method
            + " "
            + (quote(url.path) or "/")
            + ("?" + quote_plus(url.query) if url.query else "")
            + " HTTP/1.0\r\n"
        ).encode("ASCII")
        + "\r\n".join(
            [f"{key}:{value}" for key, value in headers.items()] + [""]
        ).encode("latin-1")
        + b"\r\n"
    )
    if body:
        writer.write(body)
    await writer.drain()
    while chunk := await reader.read():
        if b"\r\n\r\n" in (data := data + chunk) and e is E:
            e, data = data.split(b"\r\n\r\n", 1)
            status, o = re.match(r"HTTP/.+? (\d+).*?\r\n(.*)", e.decode("LATIN-1"), 24).groups()  # type: ignore[union-attr]  # noqa: B950
            headers = dict(re.match(r"([^\s]+):\s*(.+?)\s*$", x, 24).groups() for x in o.split("\r\n"))  # type: ignore[union-attr, misc]  # noqa: B950
    writer.close()
    await writer.wait_closed()
    if "status" not in locals():
        raise AssertionError("No HTTP response received")
    return int(status), headers, data


def detect_mode(code: str) -> str:
    """Detect which mode needs to be used."""
    import __future__  # pylint: disable=import-outside-toplevel

    flags: int = ast.PyCF_ONLY_AST
    if FLUFL:
        flags |= __future__.barry_as_FLUFL.compiler_flag
    try:
        compile(code, "", "eval", flags, 0x5F3759DF)
        return "eval"
    except SyntaxError:
        compile(code, "", "exec", flags, 0x5F3759DF)
        return "exec"


def send(
    url: str | SplitResult,
    key: str,
    code: str,
    mode: str = "exec",
    session: None | str = None,
    *,
    proxy_type: None | int = None,
    proxy_addr: None | str = None,
    proxy_port: None | int = None,
    proxy_rdns: None | bool = True,
    proxy_username: None | str = None,
    proxy_password: None | str = None,
) -> tuple[int, dict[str, str], Response | str | None]:
    """Send code to the backdoor API."""
    body = code.encode("UTF-8")
    if isinstance(url, str):
        url = urlsplit(url)
    if not url.path:
        url = url._replace(path="/api/backdoor")
    key = f"Bearer {b64encode(key.encode('UTF-8')).decode('ASCII')}"
    headers = {
        "Authorization": key,
        "Accept": "application/vnd.python.pickle",
        "X-Pickle-Protocol": str(pickle.HIGHEST_PROTOCOL),
    }
    if FLUFL:
        headers["X-Future-Feature"] = "barry_as_FLUFL"
    if session:
        headers["X-Backdoor-Session"] = session
    response = asyncio.run(
        request(
            "POST",
            url._replace(path=f"{url.path.removesuffix('/')}/{mode}"),
            headers,
            body,
            proxy_type=proxy_type,
            proxy_addr=proxy_addr,
            proxy_port=proxy_port,
            proxy_rdns=proxy_rdns,
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
    )
    try:
        return (
            response[0],  # status
            response[1],  # header
            pickle.loads(response[2]),  # data  # nosec: B301
        )
    except pickle.UnpicklingError:
        return (
            response[0],
            response[1],
            None,
        )


def lisp_always_active() -> bool:
    """Return True if LISP is always active."""
    return (
        hy
        and not hy.eval(
            hy.read(
                '(* (- (* (+ 0 1) 2 3 4 5) (+ 6 7 8 9 10 11)) '  # fmt: skip
                '(int (= (. (__import__ "os.path") sep) "/")))'
            )
        )
        and not int.from_bytes(
            getattr(
                os, "洀漀搀渀愀爀甀".encode("UTF-16-BE")[::-1].decode("UTF-16-BE")
            )(1),
            "big",
        )
        // (69 // 4 - 1)
    )


def run_and_print(  # noqa: C901  # pylint: disable=too-many-arguments, too-many-locals
    url: str,
    key: str,
    code: str,
    lisp: bool = False,
    session: None | str = None,
    time_requests: bool = False,
    *,
    proxy_type: None | int = None,
    proxy_addr: None | str = None,
    proxy_port: None | int = None,
    proxy_rdns: None | bool = True,
    proxy_username: None | str = None,
    proxy_password: None | str = None,
    # pylint: disable=redefined-builtin
    print: Callable[..., None] = print,
) -> None:
    # pylint: disable=too-complex, too-many-branches
    """Run the code and print the output."""
    start_time = time.monotonic()
    if lisp or lisp_always_active():
        code = hy.disassemble(hy.read(code), True)
    try:
        response = send(
            url,
            key,
            code,
            detect_mode(code),
            session,
            proxy_type=proxy_type,
            proxy_addr=proxy_addr,
            proxy_port=proxy_port,
            proxy_rdns=proxy_rdns,
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )
    except SyntaxError as exc:
        print(
            "".join(
                traceback.format_exception_only(exc)  # type: ignore[arg-type]
            ).strip()
        )
        return
    if time_requests:
        took = time.monotonic() - start_time
        if took > 1:
            color = "91"  # red
        elif took > 0.5:
            color = "93"  # yellow
        else:
            color = "92"  # green
        print(f"\033[{color}mTook: {took:.3f}s\033[0m")
    status, headers, body = response  # pylint: disable=unused-variable
    if status >= 400:
        print(
            "\033[91m" + f"{status} {http.client.responses[status]}" + "\033[0m"
        )
    if body is None:
        return
    if isinstance(body, str):
        print("\033[91m" + body + "\033[0m")
        return
    if isinstance(body, dict):
        if isinstance(body["success"], bool):
            print(f"Success: {body['success']}")
        if isinstance(body["output"], str) and body["output"]:
            print("Output:")
            print(body["output"].strip())
        if isinstance(body["result"], SystemExit):
            raise body["result"]
        if isinstance(body["result"], tuple):
            if not body["success"]:
                print(body["result"][0])
                return
            result_obj: Any = None
            if isinstance(body["result"][1], bytes):
                try:
                    result_obj = pickle.loads(body["result"][1])  # nosec: B301
                except Exception:  # pylint: disable=broad-except
                    if sys.flags.dev_mode:
                        traceback.print_exc()
            if (
                isinstance(result_obj, tuple)
                and len(result_obj) == 2
                and result_obj[0] == "PagerTuple"
                and isinstance(result_obj[1], str)
            ):
                pydoc.pager(result_obj[1])
            else:
                print("Result:")
                print(body["result"][0])
    else:
        print("Response has unknown type!")  # type: ignore[unreachable]
        print(body)


def shellify(code: str) -> str:
    """Modify code in a way that it gets executed in a shell."""
    if not code.startswith("!"):
        return code

    code = (
        code[1:]
        .strip()
        .replace("\\", r"\\")
        .replace("\n", r"\n")
        .replace('"', r"\"")
    )
    return f"""
async def run_shell_50821273052022fbc283():
    import asyncio
    proc = await asyncio.create_subprocess_shell(
        "{code}",
        asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    output, _ = await asyncio.wait_for(proc.communicate(), 60 * 60)
    if output:
        print(output.decode("UTF-8"))
await run_shell_50821273052022fbc283()
del run_shell_50821273052022fbc283
"""


def main() -> None | int | str:  # noqa: C901  # pylint: disable=useless-return
    # pylint: disable=too-complex, too-many-branches
    # pylint: disable=too-many-locals, too-many-statements
    """Parse arguments, load the config and start the backdoor client."""
    if "--help" in sys.argv or "-h" in sys.argv:
        sys.exit(
            """

Accepted arguments:

    --dev              use a separate config for a local developing instance
    --lisp             enable Lots of Irritating Superfluous Parentheses
    --new-proxy        don't use the saved proxy
    --new-session      start a new session with saved URL and key
    --no-config        start without loading/saveing the config
    --no-patch-help    don't patch help()
    --reset-config     reset the whole config
    --timing           print the time it took to execute each command

    --help or -h       show this help message

""".strip()
        )
    for arg in sys.argv[1:]:
        if arg not in {
            "--dev",
            "--lisp",
            "--new-proxy",
            "--new-session",
            "--no-config",
            "--no-patch-help",
            "--reset-config",
            "--timing",
            "--help",
            "-h",
        }:
            print(f"Unknown argument: {arg}")
            sys.exit(64 + 4 + 1)
    file: io.IOBase
    url: None | str = None
    key: None | str = None
    session: None | str = None
    proxy_type: None | int | EllipsisType = None
    proxy_addr: None | str = None
    proxy_port: None | int = None
    proxy_rdns: None | bool = True
    proxy_username: None | str = None
    proxy_password: None | str = None
    config_pickle = os.path.join(
        os.path.expanduser(os.getenv("XDG_CONFIG_HOME") or "~/.config"),
        "an-backdoor-client/"
        + ("dev-" if "--dev" in sys.argv else "")
        + "session.pickle",
    )
    if "--reset-config" in sys.argv and os.path.exists(config_pickle):
        os.remove(config_pickle)
    if "--no-config" not in sys.argv:
        try:
            with open(config_pickle, "rb") as file:
                config = pickle.load(file)  # nosec: B301
        except FileNotFoundError:
            pass
        else:
            url = config.get("url")
            key = config.get("key")
            session = config.get("session")
            proxy_type = config.get("proxy_type")
            proxy_addr = config.get("proxy_addr")
            proxy_port = config.get("proxy_port")
            proxy_rdns = config.get("proxy_rdns")
            proxy_username = config.get("proxy_username")
            proxy_password = config.get("proxy_password")
            if "--new-session" in sys.argv:
                print(f"Using URL {url}")
            else:
                print(f"Using URL {url} with existing session {session}")
    while not url:  # pylint: disable=while-used
        url = input("URL: ").strip().rstrip("/")
        if not url:
            print("No URL given!")
        elif "://" not in url:
            if not url.startswith("//"):
                url = "//" + url
            if re.match(
                r"^(\/\/)(localhost|127\.0\.0\.1|\[::1\])(\:\d+)?(/\S*)?$", url
            ):
                url = "http:" + url
            else:
                url = "https:" + url
            print(f"Using URL {url}")

    while not key:  # pylint: disable=while-used
        key = input("Key: ").strip()
        if not key:
            print("No key given!")

    if proxy_type is None or "--new-proxy" in sys.argv:
        proxy_url_str = input("Proxy (leave empty for none): ").strip()
        if proxy_url_str:
            if "://" not in proxy_url_str:
                if not proxy_url_str.startswith("//"):
                    proxy_url_str = "//" + proxy_url_str
                proxy_url_str = "socks5:" + proxy_url_str
            proxy_url = urlsplit(proxy_url_str)
            if proxy_url.hostname:
                proxy_type = int(socks.PROXY_TYPES[proxy_url.scheme.upper()])
                proxy_addr = proxy_url.hostname
                proxy_port = proxy_url.port
                proxy_rdns = True
                proxy_username = proxy_url.username or None
                proxy_password = proxy_url.password or None
            else:
                print("Invalid proxy URL!")
        else:
            print("No proxy given!")
    if isinstance(proxy_type, EllipsisType):
        proxy_type = None
    if proxy_type is not None:
        print(
            f"Using {socks.PRINTABLE_PROXY_TYPES[proxy_type]} proxy "
            f"{proxy_addr}{f':{proxy_port}' if proxy_port else ''}"
            + (f" with username {proxy_username}" if proxy_username else "")
        )
    else:
        print("Using no proxy (use --new-proxy to be able to set one)")

    if not session or "--new-session" in sys.argv:
        session = input("Session (enter nothing for random session): ")
        if not session:
            session = str(uuid.uuid4())
        print(f"Using session {session}")

    if "--no-config" not in sys.argv:
        os.makedirs(os.path.dirname(config_pickle), exist_ok=True)
        with open(config_pickle, "wb") as file:
            pickle.dump(
                {
                    "url": url,
                    "key": key,
                    "session": session,
                    "proxy_type": proxy_type or ...,  # not None (None == ask)
                    "proxy_addr": proxy_addr,
                    "proxy_port": proxy_port,
                    "proxy_rdns": proxy_rdns,
                    "proxy_username": proxy_username,
                    "proxy_password": proxy_password,
                },
                file,
            )

    def send_to_remote(code: str, *, mode: str) -> Any:
        """Send code to the remote backdoor and return the unpickled body."""
        return send(
            url,  # type: ignore[arg-type]
            key,  # type: ignore[arg-type]
            code,
            mode,
            session,
            proxy_type=proxy_type,  # type: ignore[arg-type]
            proxy_addr=proxy_addr,
            proxy_port=proxy_port,
            proxy_rdns=proxy_rdns,
            proxy_username=proxy_username,
            proxy_password=proxy_password,
        )[2]

    if "--no-patch-help" not in sys.argv:
        body = send_to_remote(
            "def help(*args, **kwargs):\n"
            "    import io\n"
            "    import pydoc\n"
            "    helper_output = io.StringIO()\n"
            "    pydoc.Helper(io.StringIO(), helper_output)(*args, **kwargs)\n"
            "    return 'PagerTuple', helper_output.getvalue()",
            mode="exec",
        )
        if not (isinstance(body, dict) and body["success"]):
            print("\033[91mPatching help() failed!\033[0m")

    if "--lisp" in sys.argv:
        if not hy:
            sys.exit("\033[91mHy is not installed!\033[0m")
        body = send_to_remote("__import__('hy')", mode="exec")
        if not (isinstance(body, dict) and body["success"]):
            print("\033[91mInjecting Hy builtins failed!\033[0m")

    body = send_to_remote(
        "import sys\nprint('Python', sys.version, 'on', sys.platform)",
        mode="exec",
    )
    if isinstance(body, dict) and body["success"] and body["output"]:
        print(f"\033[92mConnection to {url} was successful.\033[0m")
        print(body["output"].strip())
    else:
        print("\033[91mGetting remote information failed.\033[0m")
    print(
        'Type "copyright", "credits" or '
        'use the "help" function for more information.'
    )

    # pylint: disable=import-outside-toplevel, import-error, useless-suppression
    from pyrepl.python_reader import ReaderConsole  # type: ignore[import]
    from pyrepl.python_reader import main as _main

    def _run_and_print(self: ReaderConsole, code: str) -> None:
        # pylint: disable=unused-argument
        try:
            run_and_print(
                url,  # type: ignore[arg-type]
                key,  # type: ignore[arg-type]
                shellify(code),
                "--lisp" in sys.argv,
                session,
                "--timing" in sys.argv,
                proxy_type=proxy_type,  # type: ignore[arg-type]
                proxy_addr=proxy_addr,
                proxy_port=proxy_port,
                proxy_rdns=proxy_rdns,
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
        except Exception:  # pylint: disable=broad-except
            print(
                "\033[91mAn unexpected error occurred. "
                "Please contact a developer.\033[0m"
            )
            traceback.print_exc()

    # patch the reader console to use our run function
    ReaderConsole.execute = _run_and_print

    # run the reader
    with contextlib.suppress(EOFError):
        _main(print_banner=False)
    return None


if __name__ == "__main__":
    sys.exit(main())
