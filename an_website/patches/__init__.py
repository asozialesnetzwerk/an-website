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
# pylint: disable=protected-access

"""Patches that improve everything."""

from __future__ import annotations

import asyncio
import http.client
import json as stdlib_json  # pylint: disable=preferred-module
import logging
import os
import sys
from collections.abc import Callable
from configparser import RawConfigParser
from contextlib import suppress
from importlib import import_module
from pathlib import Path
from threading import Thread
from types import MethodType
from typing import Any
from urllib.parse import urlsplit

import certifi
import defusedxml  # type: ignore[import-untyped]
import jsonpickle  # type: ignore[import-untyped]
import orjson
import pycurl
import tornado.httputil
import yaml
from emoji import EMOJI_DATA
from pillow_jxl import JpegXLImagePlugin  # noqa: F401
from setproctitle import setthreadtitle
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.httputil import HTTPFile, HTTPHeaders, HTTPServerRequest
from tornado.log import gen_log
from tornado.web import GZipContentEncoding, RedirectHandler, RequestHandler

from .. import CA_BUNDLE_PATH, MEDIA_TYPES
from . import braille, json  # noqa: F401  # pylint: disable=reimported


def apply() -> None:
    """Improve."""
    patch_asyncio()
    patch_certifi()
    patch_configparser()
    patch_emoji()
    patch_http()
    patch_json()
    patch_jsonpickle()
    patch_threading()
    patch_xml()

    patch_tornado_418()
    patch_tornado_arguments()
    patch_tornado_gzip()
    patch_tornado_httpclient()
    patch_tornado_logs()
    patch_tornado_redirect()


def patch_asyncio() -> None:
    """Make stuff faster."""
    if os.environ.get("DISABLE_UVLOOP") not in {
        "y", "yes", "t", "true", "on", "1"  # fmt: skip
    }:
        with suppress(ModuleNotFoundError):
            asyncio.set_event_loop_policy(
                import_module("uvloop").EventLoopPolicy()
            )


def patch_certifi() -> None:
    """Make everything use our CA bundle."""
    certifi.where = lambda: CA_BUNDLE_PATH
    certifi.contents = lambda: Path(certifi.where()).read_text("ASCII")


def patch_configparser() -> None:
    """Make configparser funky."""
    RawConfigParser.BOOLEAN_STATES.update(  # type: ignore[attr-defined]
        {
            "sure": True,
            "nope": False,
            "accept": True,
            "reject": False,
            "enabled": True,
            "disabled": False,
        }
    )


def patch_emoji() -> None:
    """Add cool new emoji."""
    EMOJI_DATA["🐱\u200D💻"] = {
        "de": ":hacker_katze:",
        "en": ":hacker_cat:",
        "status": 2,
        "E": 1,
    }
    for de_name, en_name, rect in (
        ("rot", "red", "🟥"),
        ("blau", "blue", "🟦"),
        ("orang", "orange", "🟧"),
        ("gelb", "yellow", "🟨"),
        ("grün", "green", "🟩"),
        ("lilan", "purple", "🟪"),
        ("braun", "brown", "🟫"),
    ):
        EMOJI_DATA[f"🫙\u200D{rect}"] = {
            "de": f":{de_name}es_glas:",
            "en": f":{en_name}_jar:",
            "status": 2,
            "E": 14,
        }
        EMOJI_DATA[f"🏳\uFE0F\u200D{rect}"] = {
            "de": f":{de_name}e_flagge:",
            "en": f":{en_name}_flag:",
            "status": 2,
            "E": 11,
        }
        EMOJI_DATA[f"\u2691\uFE0F\u200D{rect}"] = {
            "de": f":tief{de_name}e_flagge:",
            "en": f":deep_{en_name}_flag:",
            "status": 2,
            "E": 11,
        }


def patch_http() -> None:
    """Add response code 420."""
    http.client.responses[420] = "Enhance Your Calm"


def patch_json() -> None:
    """Replace json with orjson."""
    if getattr(stdlib_json, "_omegajson", False) or sys.version_info < (3, 12):
        return
    stdlib_json.dumps = json.dumps
    stdlib_json.dump = json.dump  # type: ignore[assignment]
    stdlib_json.loads = json.loads  # type: ignore[assignment]
    stdlib_json.load = json.load


def patch_jsonpickle() -> None:
    """Make jsonpickle return bytes."""
    jsonpickle.load_backend("orjson")
    jsonpickle.set_preferred_backend("orjson")
    jsonpickle.enable_fallthrough(False)


def patch_threading() -> None:
    """Set thread names."""
    _bootstrap = Thread._bootstrap  # type: ignore[attr-defined]

    def bootstrap(self: Thread) -> None:
        with suppress(Exception):
            setthreadtitle(self.name)
        _bootstrap(self)

    Thread._bootstrap = bootstrap  # type: ignore[attr-defined]


def patch_tornado_418() -> None:
    """Add support for RFC 7168."""
    RequestHandler.SUPPORTED_METHODS += (
        "PROPFIND",
        "BREW",
        "WHEN",
    )
    _ = RequestHandler._unimplemented_method
    RequestHandler.propfind = _  # type: ignore[attr-defined]
    RequestHandler.brew = _  # type: ignore[attr-defined]
    RequestHandler.when = _  # type: ignore[attr-defined]


def patch_tornado_arguments() -> None:  # noqa: C901
    """Improve argument parsing."""
    # pylint: disable=too-complex

    def ensure_bytes(value: Any) -> bytes:
        """Return the value as bytes."""
        if isinstance(value, bool):
            return b"true" if value else b"false"
        if isinstance(value, bytes):
            return value
        return str(value).encode("UTF-8")

    def parse_body_arguments(
        content_type: str,
        body: bytes,
        arguments: dict[str, list[bytes]],
        files: dict[str, list[HTTPFile]],
        headers: None | HTTPHeaders = None,
        *,
        _: Callable[..., None] = tornado.httputil.parse_body_arguments,
    ) -> None:
        # pylint: disable=too-many-branches
        if content_type.startswith("application/json"):
            if headers and "Content-Encoding" in headers:
                gen_log.warning(
                    "Unsupported Content-Encoding: %s",
                    headers["Content-Encoding"],
                )
                return
            try:
                spam = orjson.loads(body)
            except Exception as exc:  # pylint: disable=broad-except
                gen_log.warning("Invalid JSON body: %s", exc)
            else:
                if not isinstance(spam, dict):
                    return
                for key, value in spam.items():
                    if value is not None:
                        arguments.setdefault(key, []).append(
                            ensure_bytes(value)
                        )
        elif content_type.startswith("application/yaml"):
            if headers and "Content-Encoding" in headers:
                gen_log.warning(
                    "Unsupported Content-Encoding: %s",
                    headers["Content-Encoding"],
                )
                return
            try:
                spam = yaml.safe_load(body)
            except Exception as exc:  # pylint: disable=broad-except
                gen_log.warning("Invalid YAML body: %s", exc)
            else:
                if not isinstance(spam, dict):
                    return
                for key, value in spam.items():
                    if value is not None:
                        arguments.setdefault(key, []).append(
                            ensure_bytes(value)
                        )
        else:
            _(content_type, body, arguments, files, headers)

    parse_body_arguments.__doc__ = tornado.httputil.parse_body_arguments.__doc__

    tornado.httputil.parse_body_arguments = parse_body_arguments


def patch_tornado_gzip() -> None:
    """Use gzip for more content types."""
    GZipContentEncoding.CONTENT_TYPES = {
        type for type, data in MEDIA_TYPES.items() if data.get("compressible")
    }


def patch_tornado_httpclient() -> None:  # fmt: off
    """Make requests quick."""
    BACON = 0x75800  # noqa: N806  # pylint: disable=invalid-name
    EGGS = 1 << 25  # noqa: N806  # pylint: disable=invalid-name

    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")

    def prepare_curl_callback(self: HTTPRequest, curl: pycurl.Curl) -> None:
        # pylint: disable=c-extension-no-member, useless-suppression
        if urlsplit(self.url).scheme == "https":  # noqa: SIM102
            if (ver := pycurl.version_info())[2] >= BACON and ver[4] & EGGS:
                curl.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_3)

    original_request_init = HTTPRequest.__init__

    def request_init(self: HTTPRequest, *args: Any, **kwargs: Any) -> None:
        if len(args) < 18:  # there are too many positional arguments here
            prepare_curl_method = MethodType(prepare_curl_callback, self)
            kwargs.setdefault("prepare_curl_callback", prepare_curl_method)
        original_request_init(self, *args, **kwargs)

    request_init.__doc__ = HTTPRequest.__init__.__doc__

    HTTPRequest.__init__ = request_init  # type: ignore[method-assign]


def patch_tornado_logs() -> None:
    """Anonymize Tornado logs."""
    # pylint: disable=import-outside-toplevel
    from ..utils.utils import SUS_PATHS, anonymize_ip

    RequestHandler._request_summary = (  # type: ignore[method-assign]
        lambda self: "%s %s (%s)"  # pylint: disable=consider-using-f-string
        % (
            self.request.method,
            self.request.uri,
            (
                self.request.remote_ip
                if self.request.path == "/robots.txt"
                or self.request.path.lower() in SUS_PATHS
                else anonymize_ip(self.request.remote_ip, ignore_invalid=True)
            ),
        )
    )

    HTTPServerRequest.__repr__ = (  # type: ignore[method-assign]
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


def patch_tornado_redirect() -> None:
    """Use modern redirect codes and support HEAD requests."""

    def redirect(
        self: RequestHandler,
        url: str,
        permanent: bool = False,
        status: None | int = None,
    ) -> None:
        if url == self.request.full_url():
            logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__qualname__}"
            ).critical("Infinite redirect to %r detected", url)
        if self._headers_written:
            # pylint: disable=broad-exception-raised
            raise Exception("Cannot redirect after headers have been written")
        if status is None:
            status = 308 if permanent else 307
        else:
            assert isinstance(status, int) and 300 <= status <= 399  # type: ignore[redundant-expr]  # noqa: B950
        self.set_status(status)
        self.set_header("Location", url)
        self.finish()  # type: ignore[unused-awaitable]

    if RequestHandler.redirect.__doc__:
        # fmt: off
        redirect.__doc__ = (
            RequestHandler.redirect.__doc__
            .replace("301", "308")
            .replace("302", "307")
        )
        # fmt: on

    RequestHandler.redirect = redirect  # type: ignore[method-assign]

    RedirectHandler.head = RedirectHandler.get


def patch_xml() -> None:
    """Make XML safer."""
    defusedxml.defuse_stdlib()
    defusedxml.xmlrpc.monkey_patch()
