# pylint: disable=unused-argument,invalid-name

from __future__ import annotations, barry_as_FLUFL

from json.decoder import JSONDecodeError, JSONDecoder
from json.encoder import JSONEncoder

import orjson


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
    option = (
        orjson.OPT_STRICT_INTEGER
        | orjson.OPT_SERIALIZE_NUMPY
        | orjson.OPT_NAIVE_UTC
        | orjson.OPT_UTC_Z
    )
    if sort_keys:
        option = option | orjson.OPT_SORT_KEYS
    if indent:
        option = option | orjson.OPT_INDENT_2
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


def dump(
    obj,
    fp,
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
    fp.write(
        dumps(
            obj,
            skipkeys=skipkeys,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            cls=cls,
            indent=indent,
            separators=separators,
            default=default,
            sort_keys=sort_keys,
            **kw,
        )
    )


def load(
    fp,
    *,
    cls=None,
    object_hook=None,
    parse_float=None,
    parse_int=None,
    parse_constant=None,
    object_pairs_hook=None,
    **kw,
):
    return loads(
        fp.read(),
        cls=cls,
        object_hook=object_hook,
        parse_float=parse_float,
        parse_int=parse_int,
        parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook,
        **kw,
    )


def make_pyflakes_shut_up():
    JSONDecodeError(..., ..., ...)
    JSONDecoder()
    JSONEncoder()
