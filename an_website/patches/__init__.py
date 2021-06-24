# pylint: disable=protected-access, preferred-module, reimported, invalid-name

from __future__ import annotations, barry_as_FLUFL

import json as stdlib_json
import logging
import os
from json import dumps as stdlib_json_dumps
from json import loads as stdlib_json_loads

import ecs_logging._utils
import elasticapm.utils.cloud  # type: ignore
import elasticapm.utils.json_encoder  # type: ignore
import tornado.escape

from . import json

DIR = os.path.dirname(__file__)


def apply():
    patch_json()


def patch_json():
    logger = logging.getLogger(json.__name__)

    def dump(obj, fp, **kwargs):
        logger.debug("json.dump() has been called!", stack_info=True, stacklevel=2)
        fp.write(stdlib_json_dumps(obj, **kwargs))

    def dumps(obj, **kwargs):
        logger.debug("json.dumps() has been called!", stack_info=True, stacklevel=2)
        return stdlib_json_dumps(obj, **kwargs)

    def load(fp, **kwargs):
        logger.debug("json.load() has been called!", stack_info=True, stacklevel=2)
        return stdlib_json_loads(fp.read(), **kwargs)

    def loads(s, **kwargs):
        logger.debug("json.loads() has been called!", stack_info=True, stacklevel=2)
        return stdlib_json_loads(s, **kwargs)

    stdlib_json.dump = dump
    stdlib_json.dumps = dumps
    stdlib_json.load = load
    stdlib_json.loads = loads
    tornado.escape.json = json
    ecs_logging._utils.json = json
    elasticapm.utils.json_encoder.json = json
    elasticapm.utils.cloud.json = json
