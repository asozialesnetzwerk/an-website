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

"""The module with all the tests for the backdoor."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from io import StringIO
from multiprocessing import Pipe, Process, connection
from typing import Any

import tornado.httpclient

import an_website.backdoor.backdoor_client as bc
from an_website.backdoor.backdoor import PrintWrapper

from . import app

assert app


def _run_and_get_output(
    conn: connection.Connection,
    fun: Callable[[Any], Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    """Run a function with the arguments and get the printed output."""
    output = StringIO()
    fun_out = fun(*args, print=PrintWrapper(output), **kwargs)  # type: ignore
    conn.send((fun_out, output.getvalue()))
    conn.close()


async def run_and_get_output(
    fun: Callable[..., Any], *args: Any, **kwargs: Any
) -> tuple[Any, str]:
    """Run a function with the arguments and get the printed output."""
    parent_conn, child_conn = Pipe()
    process = Process(
        target=_run_and_get_output,
        args=(child_conn, fun, *args),
        kwargs=kwargs,
    )
    process.start()
    await asyncio.sleep(1)
    text = parent_conn.recv()
    process.join()
    return text  # type: ignore


# pylint: disable=too-many-arguments
async def assert_run_and_print(
    url: str,
    command: str,
    output: None | str = None,
    lisp: bool = False,
    session: str = "69",
    assertion: None | Callable[[str], bool] = None,
) -> None:
    """Test the run_and_print function."""
    real_output = await run_and_get_output(
        bc.run_and_print,
        url,
        "xyzzy",
        command,
        lisp,
        session,
    )
    assert len(real_output) == 2
    assert real_output[0] is None
    assert isinstance(real_output[1], str)
    if assertion:
        assert assertion(real_output[1])
    else:
        assert real_output[1] == output


def get_error_assertion(error_line: str) -> Callable[[str], bool]:
    """Get the assertion lambda needed for asserting errors with the client."""
    return lambda spam: (
        spam.startswith("Traceback (most recent call last):\n")
        and spam.endswith(error_line.removesuffix("\n") + "\n")
    )


async def test_backdoor(
    http_server_client: tornado.httpclient.AsyncHTTPClient,
) -> None:
    """Test the backdoor client."""
    assert bc.E == Ellipsis
    assert bc.lisp_always_active() in {True, False}

    url = http_server_client.get_url("")  # type: ignore

    await assert_run_and_print(url, "1 & 1", "Result:\n1\n")
    await assert_run_and_print(url, "(+ 1 1)", "Result:\n2\n", True)
    await assert_run_and_print(url, "_", "Result:\n2\n")
    await assert_run_and_print(
        url, "app.settings['TRUSTED_API_SECRETS'][0]", "Result:\n'xyzzy'\n"
    )
    await assert_run_and_print(url, "print('42')", "Output:\n42\n")
    await assert_run_and_print(
        url,
        "1 1",
        'File "<unknown>", line 1\n    1 1\n      ^\n'
        "SyntaxError: invalid syntax\n",
    )
    await assert_run_and_print(
        url,
        "LOLWUT",
        assertion=get_error_assertion(
            "NameError: name 'LOLWUT' is not defined"
        ),
    )
