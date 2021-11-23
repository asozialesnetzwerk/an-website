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
import json as stdlib_json  # pylint: disable=preferred-module
import logging
import os
from json import dumps as stdlib_json_dumps  # pylint: disable=preferred-module
from json import loads as stdlib_json_loads  # pylint: disable=preferred-module

import defusedxml  # type: ignore
import ecs_logging._utils
import elasticapm.contrib.tornado.utils  # type: ignore
import elasticapm.utils  # type: ignore
import elasticapm.utils.cloud  # type: ignore
import elasticapm.utils.json_encoder  # type: ignore
import elasticsearch.connection.base
import elasticsearch.serializer
import tornado.escape
import tornado.httputil
import tornado.platform.asyncio
import tornado.web
import uvloop

from ..utils.utils import anonymize_ip
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
    anonymize_logs()


def anonymize_logs():
    """Anonymize logs."""
    tornado.web.RequestHandler._request_summary = (
        lambda self: "%s %s (%s)"  # pylint: disable=consider-using-f-string
        % (
            self.request.method,
            self.request.uri,
            anonymize_ip(self.request.remote_ip),
        )
    )
    tornado.httputil.HTTPServerRequest.__repr__ = (
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


def patch_json():
    """Replace json with orjson."""
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
