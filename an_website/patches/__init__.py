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

"""Patches that improve everything."""
from __future__ import annotations

import asyncio
import configparser
import http.client
import json as stdlib_json  # pylint: disable=preferred-module
import os
import sys

import certifi
import defusedxml  # type: ignore
import namedthreads  # type: ignore
import tornado.httpclient
import tornado.httputil
import tornado.log
import tornado.web
import uvloop
from tornado.httputil import parse_body_arguments as _parse_body_arguments

from .. import DIR as ROOT_DIR
from . import json  # pylint: disable=reimported

DIR = os.path.dirname(__file__)

# pylint: disable=protected-access


def apply() -> None:
    """Apply the patches."""
    if sys.flags.dev_mode:
        namedthreads.patch()
    defusedxml.defuse_stdlib()
    defusedxml.xmlrpc.monkey_patch()
    certifi.where = lambda: os.path.join(ROOT_DIR, "ca-bundle.crt")
    configparser.RawConfigParser.BOOLEAN_STATES.update(  # type: ignore[attr-defined]
        {"sure": True, "nope": False}
    )
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    tornado.httpclient.AsyncHTTPClient.configure(
        "tornado.curl_httpclient.CurlAsyncHTTPClient"
    )
    tornado.httputil.parse_body_arguments = parse_body_arguments
    tornado.web.RedirectHandler.head = tornado.web.RedirectHandler.get
    tornado.web.RequestHandler.redirect = redirect  # type: ignore[assignment]
    tornado.web.RequestHandler.SUPPORTED_METHODS = (
        tornado.web.RequestHandler.SUPPORTED_METHODS  # type: ignore[assignment]
        + (
            "PROPFIND",
            "BREW",
            "WHEN",
        )
    )
    _ = tornado.web.RequestHandler._unimplemented_method
    tornado.web.RequestHandler.propfind = _  # type: ignore[attr-defined]
    tornado.web.RequestHandler.brew = _  # type: ignore[attr-defined]
    tornado.web.RequestHandler.when = _  # type: ignore[attr-defined]
    http.client.responses[420] = "Enhance Your Calm"
    if not getattr(stdlib_json, "_omegajson", False):
        patch_json()
    anonymize_logs()


def patch_json() -> None:
    """Replace json with orjson."""
    stdlib_json.dumps = json.dumps
    stdlib_json.dump = json.dump
    stdlib_json.loads = json.loads
    stdlib_json.load = json.load


def anonymize_logs() -> None:
    """Anonymize logs."""
    # pylint: disable=import-outside-toplevel
    from ..utils.utils import anonymize_ip

    tornado.web.RequestHandler._request_summary = (  # type: ignore[assignment]
        lambda self: "%s %s (%s)"  # pylint: disable=consider-using-f-string
        % (
            self.request.method,
            self.request.uri,
            anonymize_ip(str(self.request.remote_ip)),
        )
    )
    tornado.httputil.HTTPServerRequest.__repr__ = (  # type: ignore[assignment]
        lambda self: "%s(%s)"  # pylint: disable=consider-using-f-string
        % (
            self.__class__.__name__,
            ", ".join(
                [
                    "%s=%r"  # pylint: disable=consider-using-f-string
                    % (
                        n,
                        getattr(self, n),
                    )
                    for n in ("protocol", "host", "method", "uri", "version")
                ]
            ),
        )
    )


def parse_body_arguments(  # noqa: D103
    content_type: str,
    body: bytes,
    arguments: dict[str, list[bytes]],
    files: dict[str, list[tornado.httputil.HTTPFile]],
    headers: None | tornado.httputil.HTTPHeaders = None,
) -> None:
    # pylint: disable=missing-function-docstring
    if content_type.startswith("application/json"):
        if headers and "Content-Encoding" in headers:
            tornado.log.gen_log.warning(
                "Unsupported Content-Encoding: %s", headers["Content-Encoding"]
            )
            return
        try:
            spam = json.loads(body)
        except Exception as exc:  # pylint: disable=broad-except
            tornado.log.gen_log.warning("Invalid JSON body: %s", exc)
        else:
            for key, value in spam.items():
                arguments.setdefault(key, []).append(value)
    else:
        _parse_body_arguments(content_type, body, arguments, files, headers)


def redirect(
    self: tornado.web.RequestHandler,
    url: str,
    permanent: bool = False,
    status: None | int = None,
) -> None:
    """Send a redirect to the given (optionally relative) URL.

    If the ``status`` argument is specified, that value is used as the
    HTTP status code; otherwise either 308 (permanent) or 307
    (temporary) is chosen based on the ``permanent`` argument.
    The default is 307 (temporary).
    """
    if self._headers_written:
        raise Exception("Cannot redirect after headers have been written")
    if status is None:
        status = 308 if permanent else 307
    else:
        assert isinstance(status, int) and 300 <= status <= 399
    self.set_status(status)
    self.set_header("Location", url)
    self.finish()
