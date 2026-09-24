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
# source: https://raw.githubusercontent.com/eukaryote/pytest-tornasync/006172c3a9f310d8f715113380b89aba9cd454ef/src/pytest_tornasync/plugin.py

from contextlib import closing, contextmanager
import inspect
from inspect import iscoroutinefunction

import tornado.ioloop
import tornado.testing
import tornado.simple_httpclient

import pytest


def get_test_timeout(pyfuncitem):
    timeout = pyfuncitem.config.option.async_test_timeout
    marker = pyfuncitem.get_closest_marker("timeout")
    if marker:
        timeout = marker.kwargs.get("seconds", timeout)
    return timeout


def pytest_addoption(parser):
    parser.addoption(
        "--async-test-timeout",
        type=float,
        help=("timeout in seconds before failing the test " "(default is no timeout)"),
    )
    parser.addoption(
        "--app-fixture",
        default="app",
        help=("fixture name returning a tornado application " '(default is "app")'),
    )


@pytest.mark.tryfirst
def pytest_pycollect_makeitem(collector, name, obj):
    if collector.funcnamefilter(name) and iscoroutinefunction(obj):
        return list(collector._genfunctions(name, obj))


@pytest.mark.tryfirst
def pytest_pyfunc_call(pyfuncitem):
    funcargs = pyfuncitem.funcargs
    testargs = {arg: funcargs[arg] for arg in pyfuncitem._fixtureinfo.argnames}

    if not iscoroutinefunction(pyfuncitem.obj):
        pyfuncitem.obj(**testargs)
        return True

    try:
        loop = funcargs["io_loop"]
    except KeyError:
        loop = tornado.ioloop.IOLoop.current()

    loop.run_sync(
        lambda: pyfuncitem.obj(**testargs), timeout=get_test_timeout(pyfuncitem)
    )
    return True


@pytest.fixture
def io_loop():
    """
    Create new io loop for each test, and tear it down after.
    """
    loop = tornado.ioloop.IOLoop()
    loop.make_current()
    yield loop
    loop.clear_current()
    loop.close(all_fds=True)


@pytest.fixture
def http_server_port():
    """
    Port used by `http_server`.
    """
    return tornado.testing.bind_unused_port()


@pytest.yield_fixture
def http_server(request, io_loop, http_server_port):
    """Start a tornado HTTP server that listens on all available interfaces.

    You must create an `app` fixture, which returns
    the `tornado.web.Application` to be tested.

    Raises:
        FixtureLookupError: tornado application fixture not found
    """
    http_app = request.getfixturevalue(request.config.option.app_fixture)
    server = tornado.httpserver.HTTPServer(http_app)
    server.add_socket(http_server_port[0])

    yield server

    server.stop()

    if hasattr(server, "close_all_connections"):
        io_loop.run_sync(
            server.close_all_connections,
            timeout=request.config.option.async_test_timeout,
        )


class AsyncHTTPServerClient(tornado.simple_httpclient.SimpleAsyncHTTPClient):
    def initialize(self, *, http_server=None):
        super().initialize()
        self._http_server = http_server

    def fetch(self, path, **kwargs):
        """
        Fetch `path` from test server, passing `kwargs` to the `fetch`
        of the underlying `tornado.simple_httpclient.SimpleAsyncHTTPClient`.
        """
        return super().fetch(self.get_url(path), **kwargs)

    def get_protocol(self):
        return "http"

    def get_http_port(self):
        for sock in self._http_server._sockets.values():
            return sock.getsockname()[1]

    def get_url(self, path):
        return "%s://127.0.0.1:%s%s" % (self.get_protocol(), self.get_http_port(), path)


@pytest.fixture
def http_server_client(http_server):
    """
    Create an asynchronous HTTP client that can fetch from `http_server`.
    """
    with closing(AsyncHTTPServerClient(http_server=http_server)) as client:
        yield client


@pytest.fixture
def http_client(http_server):
    """
    Create an asynchronous HTTP client that can fetch from anywhere.
    """
    with closing(tornado.httpclient.AsyncHTTPClient()) as client:
        yield client
