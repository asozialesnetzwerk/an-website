# The MIT License (MIT)
#
# Copyright (c) 2016 eukaryote
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# pylint: disable=line-too-long, unused-argument
# source: https://raw.githubusercontent.com/eukaryote/pytest-tornasync/006172c3a9f310d8f715113380b89aba9cd454ef/src/pytest_tornasync/plugin.py

"""Vendored pytest-tornasync pytest plugin."""

import asyncio
import contextlib
import socket
import traceback
from asyncio import AbstractEventLoop
from collections.abc import Awaitable, Generator, Iterable
from contextlib import closing
from inspect import iscoroutinefunction
from typing import Final

import pytest
import tornado.ioloop
import tornado.simple_httpclient
import tornado.testing
from pytest import (
    Class,
    Collector,
    Config,
    FixtureRequest,
    Function,
    Item,
    Module,
)
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.httpserver import HTTPServer

from an_website.main import get_default_event_loop_factory

ASYNC_TEST_TIMEOUT: Final[int] = 20
CLOSE_CONNS_TIMEOUT: Final[int] = 5
APP_FIXTURE_NAME: Final[str] = "app"
TIMEOUT_MARKER: Final[str] = "timeout"


# SEE: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_configure
def pytest_configure(config: Config) -> None:
    """Register an additional marker."""
    config.addinivalue_line(
        "markers", f"{TIMEOUT_MARKER}(seconds): Set the timeout of the test"
    )


# SEE: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_pycollect_makeitem
@pytest.hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(
    collector: Module | Class, name: str, obj: object
) -> None | Item | Collector | list[Item | Collector]:
    """Return a custom item/collector for a Python object in a module, or None."""
    if collector.funcnamefilter(name) and iscoroutinefunction(obj):
        # pylint: disable-next=protected-access
        return list(collector._genfunctions(name, obj))
    return None


async def run_with_timeout[T](  # noqa: D103
    future: Awaitable[T], *, timeout: int
) -> T:
    """Await a future with a timeout."""
    async with asyncio.timeout(timeout):
        return await future


# SEE: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_pyfunc_call
@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: Function) -> object | None:
    """Call underlying test function."""
    funcargs = pyfuncitem.funcargs
    # pylint: disable-next=protected-access
    testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}

    if not iscoroutinefunction(pyfuncitem.obj):
        pyfuncitem.obj(**testargs)
        return True

    markers = list(pyfuncitem.iter_markers(TIMEOUT_MARKER))
    if markers:
        [marker] = markers
        [timeout] = marker.args
    else:
        timeout = ASYNC_TEST_TIMEOUT

    future = pyfuncitem.obj(**testargs)
    if timeout is not None:
        future = run_with_timeout(future, timeout=timeout)

    try:
        loop = asyncio.get_event_loop()
    except Exception:  # pylint: disable=broad-exception-caught
        traceback.print_exc()
        # Create new event loop as no event loop is running
        with contextlib.contextmanager(_io_loop)() as loop:
            loop.run_until_complete(future)
    else:
        # if io_loop fixture argument is present, it should be the running loop
        if (_l := funcargs.get("io_loop")) is not None:
            assert _l is loop

        loop.run_until_complete(future)

    return True


def _io_loop() -> Generator[AbstractEventLoop]:
    """Create new io loop for each test, and tear it down after."""
    loop = get_default_event_loop_factory()()
    asyncio.set_event_loop(loop)
    yield loop
    asyncio.set_event_loop(None)
    loop.stop()
    loop.close()


io_loop = pytest.fixture(_io_loop)


@pytest.fixture
def http_server_port() -> tuple[socket.socket, int]:
    """Port used by `http_server`."""
    return tornado.testing.bind_unused_port()


@pytest.fixture
def http_server(
    request: FixtureRequest,
    io_loop: AbstractEventLoop,
    http_server_port: tuple[socket.socket, int],
) -> Iterable[object]:
    """Start a tornado HTTP server that listens on all available interfaces.

    You must create an `app` fixture, which returns
    the `tornado.web.Application` to be tested.

    Raises:
        FixtureLookupError: tornado application fixture not found
    """
    http_app = request.getfixturevalue(APP_FIXTURE_NAME)
    server = tornado.httpserver.HTTPServer(http_app)
    server.add_socket(http_server_port[0])

    yield server

    server.stop()

    if hasattr(server, "close_all_connections"):
        future = run_with_timeout(
            server.close_all_connections(), timeout=CLOSE_CONNS_TIMEOUT
        )
        io_loop.run_until_complete(future)


@pytest.fixture
def http_client(http_server: HTTPServer) -> Iterable[CurlAsyncHTTPClient]:
    """Create an asynchronous HTTP client that can fetch from anywhere."""
    with closing(
        CurlAsyncHTTPClient(max_clients=1, force_instance=True)
    ) as client:
        yield client
