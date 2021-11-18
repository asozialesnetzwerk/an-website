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
import hashlib
import json as stdlib_json  # pylint: disable=preferred-module
import logging
import os
import time
from json import dumps as stdlib_json_dumps  # pylint: disable=preferred-module
from json import loads as stdlib_json_loads  # pylint: disable=preferred-module
from typing import Optional

import defusedxml  # type: ignore
import ecs_logging._utils
import elasticapm.utils.cloud  # type: ignore
import elasticapm.utils.json_encoder  # type: ignore
import elasticsearch.connection.base
import elasticsearch.serializer
import tornado.escape
import tornado.httputil
import tornado.platform.asyncio
import tornado.web
import uvloop

from . import json  # pylint: disable=reimported

DIR = os.path.dirname(__file__)

# pylint: disable=protected-access, invalid-name


def apply():
    """Apply the patches."""
    patch_json()
    defusedxml.defuse_stdlib()
    configparser.RawConfigParser.BOOLEAN_STATES.update(  # type: ignore
        {"sure": True, "nope": False}
    )
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    tornado.web.RequestHandler.SUPPORTED_METHODS = (
        tornado.web.RequestHandler.SUPPORTED_METHODS
        + (
            "PROPFIND",
            "BREW",
            "WHEN",
        )
    )
    patch_ip_hashing()


def patch_ip_hashing():
    """Hash the remote_ip before it can get accessed."""
    salt = [os.urandom(32), time.time()]

    init = tornado.httputil.HTTPServerRequest.__init__  # type: ignore

    def init_http_server_request(  # pylint: disable=too-many-arguments
        self,
        method: Optional[str] = None,
        uri: Optional[str] = None,
        version: str = "HTTP/1.0",
        headers: Optional["tornado.HTTPHeaders"] = None,  # type: ignore
        body: Optional[bytes] = None,
        host: Optional[str] = None,
        files: Optional[  # type: ignore
            dict[str, list["tornado.HTTPFile"]]
        ] = None,
        connection: Optional["tornado.HTTPConnection"] = None,  # type: ignore
        start_line: Optional[  # type: ignore
            "tornado.RequestStartLine"
        ] = None,
        server_connection: Optional[object] = None,
    ) -> None:
        """Initialize a HTTP server request."""
        init(
            self,
            method,
            uri,
            version,
            headers,
            body,
            host,
            files,
            connection,
            start_line,
            server_connection,
        )
        if self.remote_ip not in ("127.0.0.1", "::1", None):
            self.remote_ip = hashlib.sha1(
                self.remote_ip.encode() + salt[0]
            ).hexdigest()[:16]
            # if salt[1] is more than one day ago
            if salt[1] < time.monotonic() - (24 * 60 * 60):
                salt[0] = os.urandom(32)
                salt[1] = time.monotonic()
        if "X-Forwarded-For" in self.headers:
            self.headers["X-Forwarded-For"] = self.remote_ip
        if "X-Real-IP" in self.headers:
            self.headers["X-Real-IP"] = self.remote_ip

    tornado.httputil.HTTPServerRequest.__init__ = init_http_server_request


def patch_json():
    """Patch json."""
    logger = logging.getLogger(json.__name__)

    def dump(obj, fp, **kwargs):
        logger.debug(
            "json.dump() has been called!", stack_info=True, stacklevel=2
        )
        fp.write(stdlib_json_dumps(obj, **kwargs))

    def dumps(obj, **kwargs):
        logger.debug(
            "json.dumps() has been called!", stack_info=True, stacklevel=2
        )
        return stdlib_json_dumps(obj, **kwargs)

    def load(fp, **kwargs):
        logger.debug(
            "json.load() has been called!", stack_info=True, stacklevel=2
        )
        return stdlib_json_loads(fp.read(), **kwargs)

    def loads(s, **kwargs):
        logger.debug(
            "json.loads() has been called!", stack_info=True, stacklevel=2
        )
        return stdlib_json_loads(s, **kwargs)

    stdlib_json.dump = dump
    stdlib_json.dumps = dumps
    stdlib_json.load = load
    stdlib_json.loads = loads

    ecs_logging._utils.json = json
    elasticapm.utils.cloud.json = json
    elasticapm.utils.json_encoder.json = json
    elasticsearch.connection.base.json = json
    elasticsearch.serializer.json = json
    tornado.escape.json = json
