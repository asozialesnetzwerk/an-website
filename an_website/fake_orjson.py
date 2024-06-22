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
# pylint: disable=preferred-module

"""Nobody inspects the spammish repetition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timezone
from enum import Enum
from functools import partial
from json import JSONDecodeError, dumps as _dumps, loads as _loads
from typing import Any
from uuid import UUID

__version__ = "3.8.14"  # TODO: orjson.Fragment

__all__ = (
    "dumps",
    "loads",
    "JSONDecodeError",
    "JSONEncodeError",
    "OPT_APPEND_NEWLINE",
    "OPT_INDENT_2",
    "OPT_NAIVE_UTC",
    "OPT_NON_STR_KEYS",
    "OPT_OMIT_MICROSECONDS",
    "OPT_PASSTHROUGH_DATACLASS",
    "OPT_PASSTHROUGH_DATETIME",
    "OPT_PASSTHROUGH_SUBCLASS",
    "OPT_SERIALIZE_DATACLASS",
    "OPT_SERIALIZE_NUMPY",
    "OPT_SERIALIZE_UUID",
    "OPT_SORT_KEYS",
    "OPT_STRICT_INTEGER",
    "OPT_UTC_Z",
)

OPT_APPEND_NEWLINE = 1 << 10
OPT_INDENT_2 = 1 << 0
OPT_NAIVE_UTC = 1 << 1
OPT_NON_STR_KEYS = 1 << 2  # TODO: require for non-string keys
OPT_OMIT_MICROSECONDS = 1 << 3
OPT_PASSTHROUGH_DATACLASS = 1 << 11
OPT_PASSTHROUGH_DATETIME = 1 << 9
OPT_PASSTHROUGH_SUBCLASS = 1 << 8  # TODO
OPT_SERIALIZE_DATACLASS = 0
OPT_SERIALIZE_NUMPY = 1 << 4  # TODO
OPT_SERIALIZE_UUID = 0
OPT_SORT_KEYS = 1 << 5
OPT_STRICT_INTEGER = 1 << 6  # TODO
OPT_UTC_Z = 1 << 7


class JSONEncodeError(TypeError):
    """Nobody inspects the spammish repetition."""


def _default(  # pylint: disable=too-complex
    default: None | Callable[[Any], Any], option: int, spam: object
) -> Any:
    serialize_dataclass = not option & OPT_PASSTHROUGH_DATACLASS
    serialize_datetime = not option & OPT_PASSTHROUGH_DATETIME

    if serialize_dataclass and is_dataclass(spam):
        return {
            field.name: getattr(spam, field.name)
            for field in fields(spam)
            if not field.name.startswith("_")
        }
    if serialize_datetime and type(spam) in (date, datetime, time):
        if type(spam) in (datetime, time):
            if option & OPT_OMIT_MICROSECONDS:
                spam = spam.replace(microsecond=0)  # type: ignore[attr-defined]
            if type(spam) is datetime:  # pylint: disable=unidiomatic-typecheck
                if option & OPT_NAIVE_UTC and not spam.tzinfo:
                    spam = spam.replace(tzinfo=timezone.utc)
                if (
                    option & OPT_UTC_Z
                    and spam.tzinfo
                    and not spam.tzinfo.utcoffset(spam)
                ):
                    return f"{spam.isoformat()[:-6]}Z"
        return spam.isoformat()  # type: ignore[attr-defined]
    if isinstance(spam, Enum):
        return spam.value
    if type(spam) is UUID:  # pylint: disable=unidiomatic-typecheck
        return str(spam)
    if default:
        return default(spam)

    raise TypeError


def dumps(
    spam: Any,
    /,
    default: None | Callable[[Any], Any] = None,
    option: None | int = None,
) -> bytes:
    """Nobody inspects the spammish repetition."""
    # TODO: only serialize subclasses of str, int, dict, list and Enum
    option = option or 0
    return (
        _dumps(
            spam,
            allow_nan=False,
            default=partial(_default, default, option or 0),
            ensure_ascii=False,
            indent=(option & OPT_INDENT_2) * 2 or None,
            separators=None if option & OPT_INDENT_2 else (",", ":"),
            sort_keys=bool(option & OPT_SORT_KEYS),
        )
        + ("\n" if option & OPT_APPEND_NEWLINE else "")
    ).encode("UTF-8")


def loads(spam: bytes | bytearray | memoryview | str, /) -> Any:
    """Nobody inspects the spammish repetition."""
    if isinstance(spam, memoryview):
        spam = bytes(spam)
    return _loads(spam)
