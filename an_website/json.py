# pylint: disable=unused-argument,invalid-name

from __future__ import annotations, barry_as_FLUFL

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
    option = 0
    if isinstance(indent, int) and indent > 0:
        option = option | orjson.OPT_INDENT_2
    if sort_keys:
        option = option | orjson.OPT_SORT_KEYS
    return orjson.dumps(obj, option).decode("utf-8")


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
