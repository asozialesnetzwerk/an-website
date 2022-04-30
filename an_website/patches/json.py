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

"""A very fast JSON implementation."""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from json.encoder import JSONEncoder
from typing import IO, Any, Protocol, TypeVar

import orjson

_T_co = TypeVar("_T_co", covariant=True)


class SupportsRead(Protocol[_T_co]):  # noqa: D101
    # pylint: disable=missing-class-docstring, too-few-public-methods
    def read(self, __length: int = ...) -> _T_co:
        # pylint: disable=missing-function-docstring
        ...


def get_caller_name() -> None | str:  # noqa: D103
    # pylint: disable=missing-function-docstring
    try:
        frame = inspect.currentframe()
        frame = frame.f_back if frame else None
        if not (frame and "__name__" in frame.f_globals):
            return None
        name = frame.f_globals["__name__"]
        while (  # pylint: disable=while-used
            frame
            and "__name__" in frame.f_globals
            and frame.f_globals["__name__"] == name
        ):
            frame = frame.f_back
        caller = (
            frame.f_globals["__name__"]
            if frame and "__name__" in frame.f_globals
            else None
        )
    finally:
        del frame
    return caller  # type: ignore[no-any-return]


def dumps(  # noqa: C901, D103
    obj: Any,
    *,
    skipkeys: bool = False,
    ensure_ascii: bool = True,
    check_circular: bool = True,
    allow_nan: bool = True,
    cls: None | type[JSONEncoder] = None,
    indent: None | int | str = None,
    separators: None | tuple[str, str] = None,
    default: None | Callable[[Any], Any] = None,
    sort_keys: bool = False,
    **kwargs: Any,
) -> str:
    # pylint: disable=missing-function-docstring
    output: str | bytes
    caller = get_caller_name()
    option = orjson.OPT_SERIALIZE_NUMPY
    if caller == "tornado.escape":
        option |= orjson.OPT_NAIVE_UTC | orjson.OPT_UTC_Z
    else:
        option |= orjson.OPT_PASSTHROUGH_DATACLASS
    if sort_keys:
        option |= orjson.OPT_SORT_KEYS
    if indent is not None:
        option |= orjson.OPT_INDENT_2
    if cls is not None:
        _ = cls(
            skipkeys=skipkeys,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            indent=indent,  # type: ignore[arg-type]
            separators=separators,
            default=default,
            sort_keys=sort_keys,
            **kwargs,
        )
        default = _.default
    output = orjson.dumps(obj, default, option)
    if indent is not None and indent not in {2, "  "}:
        if isinstance(indent, int):
            indent = " " * indent
        output = re.sub(
            rb"(?m)^\s+",
            lambda match: match.group(0).replace(
                b"  ", str(indent).encode("utf-8")
            ),
            output,
        )
    if caller != "elasticsearch.serializer":
        output = output.decode("utf-8")
    return output  # type: ignore[return-value]


def dump(obj: Any, fp: IO[str], **kwargs: Any) -> None:  # noqa: D103
    # pylint: disable=invalid-name, missing-function-docstring
    fp.write(dumps(obj, **kwargs))


def loads(s: str | bytes, **kwargs: Any) -> Any:  # noqa: D103
    # pylint: disable=invalid-name, missing-function-docstring, unused-argument
    return orjson.loads(s)


def load(fp: SupportsRead[str | bytes], **kwargs: Any) -> Any:  # noqa: D103
    # pylint: disable=invalid-name, missing-function-docstring, unused-argument
    return loads(fp.read())
