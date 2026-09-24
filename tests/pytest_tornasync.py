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

import socket
from collections.abc import Iterable
from contextlib import closing
from inspect import iscoroutinefunction
from typing import Any, Final, cast

import pytest
import tornado.ioloop
import tornado.simple_httpclient
import tornado.testing
from coverage.collector import Collector
from pytest import (
    Class,
    FixtureRequest,
    Function,
    Item,
    Module,
    Parser,
    PytestPluginManager,
)
from tornado.concurrent import Future
from tornado.httpclient import AsyncHTTPClient, HTTPResponse
from tornado.httpserver import HTTPServer

ASYNC_TEST_TIMEOUT: Final[int] = 20
APP_FIXTURE_NAME: Final[str] = "app"


# SEE: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_addoption
def pytest_addoption(
    parser: Parser, pluginmanager: PytestPluginManager
) -> None:
    """Register argparse-style options."""


# SEE: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_pycollect_makeitem
@pytest.mark.tryfirst
def pytest_pycollect_makeitem(
    collector: Module | Class, name: str, obj: object
) -> None | Item | Collector | list[Item | Collector]:
    """Return a custom item/collector for a Python object in a module, or None."""
    if collector.funcnamefilter(name) and iscoroutinefunction(obj):
        # pylint: disable-next=protected-access
        return list(collector._genfunctions(name, obj))
    return None


# SEE: https://docs.pytest.org/en/stable/reference/reference.html#pytest.hookspec.pytest_pyfunc_call
@pytest.mark.tryfirst
def pytest_pyfunc_call(pyfuncitem: Function) -> object | None:
    """Call underlying test function."""
    funcargs = pyfuncitem.funcargs
    # pylint: disable-next=protected-access
    testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}

    if not iscoroutinefunction(pyfuncitem.obj):
        pyfuncitem.obj(**testargs)
        return True

    loop: tornado.ioloop.IOLoop
    try:
        loop = cast(Any, funcargs["io_loop"])
    except KeyError:
        loop = tornado.ioloop.IOLoop.current()

    loop.run_sync(
        lambda: pyfuncitem.obj(**testargs), timeout=ASYNC_TEST_TIMEOUT
    )
    return True


@pytest.fixture
def io_loop() -> Iterable[tornado.ioloop.IOLoop]:
    """Create new io loop for each test, and tear it down after."""
    loop = tornado.ioloop.IOLoop()
    loop.make_current()
    yield loop
    loop.clear_current()
    loop.close(all_fds=True)


@pytest.fixture
def http_server_port() -> tuple[socket.socket, int]:
    """Port used by `http_server`."""
    return tornado.testing.bind_unused_port()


@pytest.fixture
def http_server(
    request: FixtureRequest,
    io_loop: tornado.ioloop.IOLoop,
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
        io_loop.run_sync(
            server.close_all_connections,
            timeout=ASYNC_TEST_TIMEOUT,
        )


class AsyncHTTPServerClient(tornado.simple_httpclient.SimpleAsyncHTTPClient):
    """Wrapper around AsyncHTTPClient."""

    _http_server: HTTPServer

    # pylint: disable-next=redefined-outer-name,arguments-differ
    def initialize(self, *, http_server: HTTPServer) -> None:  # type: ignore[override]
        """Initialize self."""
        super().initialize()
        self._http_server = http_server

    # pylint: disable-next=arguments-differ
    def fetch(  # type: ignore[override]
        self,
        request: str,
        **kwargs: Any,
    ) -> Future[HTTPResponse]:
        """
        Fetch local path.

        Fetch `path` from test server, passing `kwargs` to the `fetch`
        of the underlying `tornado.simple_httpclient.SimpleAsyncHTTPClient`.
        """
        return super().fetch(self.get_url(request), **kwargs)

    def get_protocol(self) -> str:
        """Get the protocol."""
        # pylint: disable=no-self-use
        return "http"

    def get_http_port(self) -> None | int:
        """Get the HTTP port."""
        # pylint: disable-next=protected-access
        for sock in self._http_server._sockets.values():
            return cast(int, sock.getsockname()[1])
        return None

    def get_url(self, path: str) -> str:
        """Get the full URL for a given path."""
        return f"{self.get_protocol()}://127.0.0.1:{self.get_http_port()}{path}"


@pytest.fixture
def http_server_client(
    http_server: HTTPServer,
) -> Iterable[AsyncHTTPServerClient]:
    """Create an asynchronous HTTP client that can fetch from `http_server`."""
    with closing(AsyncHTTPServerClient(http_server=http_server)) as client:
        yield client


@pytest.fixture
def http_client(http_server: HTTPServer) -> Iterable[AsyncHTTPClient]:
    """Create an asynchronous HTTP client that can fetch from anywhere."""
    with closing(tornado.httpclient.AsyncHTTPClient()) as client:
        yield client
