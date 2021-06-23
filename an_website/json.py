# pylint: disable=unused-argument,invalid-name

from __future__ import annotations, barry_as_FLUFL

from json.decoder import JSONDecoder, JSONDecodeError
from json.encoder import JSONEncoder

import ecs_logging._utils
import elasticapm.utils.json_encoder
import elasticapm.utils.cloud
import orjson
import tornado.escape

from . import json  # pylint: disable=import-self


def dumps(
    obj,
    *,
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    cls=None,
    indent=None,
    separators=None,
    default=None,
    sort_keys=False,
    **kw,
):
    if cls is not None:
        _ = cls(
            skipkeys=skipkeys,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            indent=indent,
            separators=separators,
            default=default,
            sort_keys=sort_keys,
            **kw,
        )
        default = lambda o: _.default(_, o)
    option = orjson.OPT_UTC_Z
    if indent:
        option = option | orjson.OPT_INDENT_2
    if sort_keys:
        option = option | orjson.OPT_SORT_KEYS
    return orjson.dumps(obj, default, option).decode("utf-8")


def loads(
    s,
    *,
    cls=None,
    object_hook=None,
    parse_float=None,
    parse_int=None,
    parse_constant=None,
    object_pairs_hook=None,
    **kw,
):
    return orjson.loads(s)


def patch():
    escape.json = json
    ecs_logging._utils.json = json
    elasticapm.utils.json_encoder.json = json
    elasticapm.utils.cloud = json
    
