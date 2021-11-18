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
import elasticapm.conf.constants
import elasticapm.contrib.tornado.utils
import elasticapm.utils
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
from .utils.utils import anonymize_ip

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


def elasticapm_get_data_from_request(request_handler, request, config, event_type):
    """Capture relevant data from a tornado.httputil.HTTPServerRequest."""
    result = {
        "method": request.method,
        "socket": {"remote_address": anonymize_ip(request.remote_ip)},
        "cookies": request.cookies,
        "http_version": request.version,
    }
    if config.capture_headers:
        result["headers"] = dict(request.headers)
        if "X-Real-IP" in result["headers"]:
            result["headers"]["X-Real-IP"] = anonymize_ip(
                result["headers"]["X-Real-IP"]
            )
        if "X-Forwarded-For" in result["headers"]:
            if "," in result["headers"]["X-Forwarded-For"]:
                result["headers"]["X-Forwarded-For"] = anonymize_ip(
                    result["headers"]["X-Forwarded-For"].split(",")
                )
            else:
                result["headers"]["X-Forwarded-For"] = anonymize_ip(
                    result["headers"]["X-Forwarded-For"]
                )
        if "CF-Connecting-IP" in result["headers"]:
            result["headers"]["CF-Connecting-IP"] = anonymize_ip(
                result["headers"]["CF-Connecting-IP"]
            )
        if "True-Client-IP" in result["headers"]:
            result["headers"]["True-Client-IP"] = anonymize_ip(
                result["headers"]["True-Client-IP"]
            )
    if request.method in elasticapm.conf.constants.HTTP_WITH_BODY:
        if tornado.web._has_stream_request_body(request_handler.__class__):
            result["body"] = (
                "[STREAMING]"
                if config.capture_body in ("all", event_type)
                else "[REDACTED]"
            )
        else:
            body = None
            try:
                body = tornado.escape.json_decode(request.body)
            except Exception:
                body = str(request.body, errors="ignore")
            if body is not None:
                result["body"] = (
                    body
                    if config.capture_body in ("all", event_type)
                    else "[REDACTED]"
                )
    result["url"] = elasticapm.utils.get_url_dict(request.full_url())
    return result


def anonymize_logs():
    """Anonymize logs."""

    elasticapm.contrib.tornado.utils.get_data_from_request = (
        elasticapm_get_data_from_request
    )

    tornado.web._request_summary = lambda self: "%s %s (%s)" % (
        self.request.method,
        self.request.uri,
        anonymize_ip(self.request.remote_ip),
    )


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
