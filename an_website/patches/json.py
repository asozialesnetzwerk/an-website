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
from collections.abc import Callable
from json.encoder import JSONEncoder
from typing import IO, Any, Protocol, TypeVar

import orjson
import regex

_T_co = TypeVar("_T_co", covariant=True)


class SupportsRead(Protocol[_T_co]):  # noqa: D101
    # pylint: disable=missing-class-docstring, too-few-public-methods
    def read(self, __length: int = ...) -> _T_co:  # noqa: D102
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
            frame and frame.f_globals.get("__name__") == name  # type: ignore[truthy-bool]  # noqa: B950
        ):
            frame = frame.f_back
        caller = frame.f_globals.get("__name__") if frame else None
    finally:
        del frame
    return caller


def dumps(  # noqa: D103  # pylint: disable=too-many-arguments
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
            indent=indent,
            separators=separators,
            default=default,
            sort_keys=sort_keys,
            **kwargs,
        )
        default = _.default
    output = orjson.dumps(obj, default, option)
    if indent not in {None, 2, "  "}:
        if isinstance(indent, int):
            indent = " " * indent
        indent_bytes = str(indent).encode("UTF-8")
        output = regex.sub(
            rb"(?m)^\s+",
            lambda match: len(match[0]) // 2 * indent_bytes,
            output,
        )
    return output.decode("UTF-8")


def dump(obj: Any, fp: IO[str], **kwargs: Any) -> None:  # noqa: D103
    # pylint: disable=missing-function-docstring
    fp.write(dumps(obj, **kwargs))


def loads(s: str | bytes, **kwargs: Any) -> Any:  # noqa: D103
    # pylint: disable=missing-function-docstring, unused-argument
    return orjson.loads(s)


def load(fp: SupportsRead[str | bytes], **kwargs: Any) -> Any:  # noqa: D103
    # pylint: disable=missing-function-docstring, unused-argument
    return loads(fp.read())
