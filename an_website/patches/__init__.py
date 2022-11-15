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

import contextlib
import http.client
import json as stdlib_json  # pylint: disable=preferred-module
import os
from asyncio import set_event_loop_policy
from collections.abc import Callable
from configparser import RawConfigParser
from pathlib import Path
from threading import Thread
from typing import Any, Final

import certifi
import defusedxml  # type: ignore[import]
import orjson
import tornado.httputil
import yaml
from emoji import EMOJI_DATA
from emoji import unicode_codes as euc
from setproctitle import setthreadtitle
from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import HTTPFile, HTTPHeaders, HTTPServerRequest
from tornado.log import gen_log
from tornado.web import GZipContentEncoding, RedirectHandler, RequestHandler

from .. import DIR as ROOT_DIR
from .. import MEDIA_TYPES
from . import braille, json  # noqa: F401  # pylint: disable=reimported

DIR: Final = os.path.dirname(__file__)

with contextlib.suppress(ImportError):
    # pylint: disable=import-error, useless-suppression
    from jxlpy import JXLImagePlugin  # type: ignore[import]  # noqa: F401

_bootstrap = Thread._bootstrap  # type: ignore[attr-defined]


def _boobstrap(self: Thread) -> None:
    with contextlib.suppress(Exception):
        setthreadtitle(self.name)
    _bootstrap(self)


def apply() -> None:
    """Apply the patches."""
    defusedxml.defuse_stdlib()
    defusedxml.xmlrpc.monkey_patch()
    Thread._bootstrap = _boobstrap  # type: ignore[attr-defined]
    certifi.where = lambda: os.path.join(ROOT_DIR, "ca-bundle.crt")
    certifi.contents = lambda: Path(certifi.where()).read_text("ASCII")
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
    # pylint: disable=import-outside-toplevel
    if "DISABLE_UVLOOP" not in os.environ:
        from uvloop import EventLoopPolicy

        set_event_loop_policy(EventLoopPolicy())
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    tornado.httputil.parse_body_arguments = parse_body_arguments
    RedirectHandler.head = RedirectHandler.get
    RequestHandler.redirect = redirect  # type: ignore[assignment]
    RequestHandler.SUPPORTED_METHODS = (
        RequestHandler.SUPPORTED_METHODS  # type: ignore[assignment]
        + (
            "PROPFIND",
            "BREW",
            "WHEN",
        )
    )
    _ = RequestHandler._unimplemented_method
    RequestHandler.propfind = _  # type: ignore[attr-defined]
    RequestHandler.brew = _  # type: ignore[attr-defined]
    RequestHandler.when = _  # type: ignore[attr-defined]
    GZipContentEncoding.CONTENT_TYPES = {
        type for type, data in MEDIA_TYPES.items() if data.get("compressible")
    }
    http.client.responses[420] = "Enhance Your Calm"
    if not getattr(stdlib_json, "_omegajson", False):
        patch_json()
    anonymize_logs()
    patch_emoji()


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
    for lang in euc.LANGUAGES:
        euc._EMOJI_UNICODE[lang] = None  # type: ignore[attr-defined]
    euc._ALIASES_UNICODE.clear()  # type: ignore[attr-defined]


def patch_json() -> None:
    """Replace json with orjson."""
    stdlib_json.dumps = json.dumps
    stdlib_json.dump = json.dump
    stdlib_json.loads = json.loads
    stdlib_json.load = json.load


def anonymize_logs() -> None:
    """Anonymize logs."""
    # pylint: disable=import-outside-toplevel
    from ..utils.utils import SUS_PATHS, anonymize_ip

    RequestHandler._request_summary = (  # type: ignore[assignment]
        lambda self: "%s %s (%s)"  # pylint: disable=consider-using-f-string
        % (
            self.request.method,
            self.request.uri,
            self.request.remote_ip
            if self.request.path == "/robots.txt"
            or self.request.path.lower() in SUS_PATHS
            else anonymize_ip(self.request.remote_ip, ignore_invalid=True),
        )
    )

    HTTPServerRequest.__repr__ = (  # type: ignore[assignment]
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


def ensure_bytes(value: Any) -> bytes:
    """Return the value as bytes."""
    if isinstance(value, bool):
        return b"true" if value else b"false"
    if isinstance(value, bytes):
        return value
    return str(value).encode("UTF-8")


def parse_body_arguments(  # noqa: D103, C901
    content_type: str,
    body: bytes,
    arguments: dict[str, list[bytes]],
    files: dict[str, list[HTTPFile]],
    headers: None | HTTPHeaders = None,
    *,
    _: Callable[..., None] = tornado.httputil.parse_body_arguments,
) -> None:
    # pylint: disable=missing-function-docstring, too-complex, too-many-branches
    if content_type.startswith("application/json"):
        if headers and "Content-Encoding" in headers:
            gen_log.warning(
                "Unsupported Content-Encoding: %s", headers["Content-Encoding"]
            )
            return
        try:
            spam = orjson.loads(body)
        except Exception as exc:  # pylint: disable=broad-except
            gen_log.warning("Invalid JSON body: %s", exc)
        else:
            for key, value in spam.items():
                if value is not None:
                    arguments.setdefault(key, []).append(ensure_bytes(value))
    elif content_type.startswith("application/yaml"):
        if headers and "Content-Encoding" in headers:
            gen_log.warning(
                "Unsupported Content-Encoding: %s", headers["Content-Encoding"]
            )
            return
        try:
            spam = yaml.safe_load(body)
        except Exception as exc:  # pylint: disable=broad-except
            gen_log.warning("Invalid YAML body: %s", exc)
        else:
            for key, value in spam.items():
                if value is not None:
                    arguments.setdefault(key, []).append(ensure_bytes(value))
    else:
        _(content_type, body, arguments, files, headers)


def redirect(
    self: RequestHandler,
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
        assert isinstance(status, int) and 300 <= status <= 399  # nosec: B101
    self.set_status(status)
    self.set_header("Location", url)
    self.finish()
