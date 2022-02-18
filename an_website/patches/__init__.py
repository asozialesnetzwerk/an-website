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

"""Patches that break everything."""
from __future__ import annotations

import asyncio
import configparser
import http.client
import json as stdlib_json  # pylint: disable=preferred-module
import os
import sys

import defusedxml  # type: ignore
import namedthreads  # type: ignore
import tornado.httputil
import tornado.platform.asyncio
import tornado.web
import uvloop

from ..utils.utils import anonymize_ip
from . import json  # pylint: disable=reimported

DIR = os.path.dirname(__file__)

# pylint: disable=protected-access


def apply() -> None:
    """Apply the patches."""
    defusedxml.defuse_stdlib()
    configparser.RawConfigParser.BOOLEAN_STATES.update(  # type: ignore
        {"sure": True, "nope": False}
    )
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    tornado.web.RequestHandler.SUPPORTED_METHODS = (
        tornado.web.RequestHandler.SUPPORTED_METHODS  # type: ignore
        + (
            "PROPFIND",
            "BREW",
            "WHEN",
        )
    )
    http.client.responses[420] = "Enhance Your Calm"
    http.client.responses[469] = "Nice Try"
    anonymize_logs()
    if not getattr(stdlib_json, "_omegajson", False):
        patch_json()
    if sys.flags.dev_mode:
        namedthreads.patch()


def anonymize_logs() -> None:
    """Anonymize logs."""
    tornado.web.RequestHandler._request_summary = (  # type: ignore
        lambda self: "%s %s (%s)"  # pylint: disable=consider-using-f-string
        % (
            self.request.method,
            self.request.uri,
            anonymize_ip(str(self.request.remote_ip)),
        )
    )
    tornado.httputil.HTTPServerRequest.__repr__ = (  # type: ignore
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


def patch_json() -> None:
    """Replace json with orjson."""
    stdlib_json.dump = json.dump
    stdlib_json.dumps = json.dumps
    stdlib_json.load = json.load
    stdlib_json.loads = json.loads
