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

"""Temporary fix for memory corruption issue related to orjson."""

from __future__ import annotations

from collections.abc import Callable
from json import JSONDecodeError
from json import dumps as _dumps
from json import loads as _loads
from typing import Any

__version__ = "0.0.0"

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

OPT_APPEND_NEWLINE = 1024
OPT_INDENT_2 = 1
OPT_NAIVE_UTC = 2
OPT_NON_STR_KEYS = 4
OPT_OMIT_MICROSECONDS = 8
OPT_PASSTHROUGH_DATACLASS = 2048
OPT_PASSTHROUGH_DATETIME = 512
OPT_PASSTHROUGH_SUBCLASS = 256
OPT_SERIALIZE_DATACLASS = 0
OPT_SERIALIZE_NUMPY = 16
OPT_SERIALIZE_UUID = 0
OPT_SORT_KEYS = 32
OPT_STRICT_INTEGER = 64
OPT_UTC_Z = 128


class JSONEncodeError(TypeError):
    """Nobody inspects the spammish repetition."""


def dumps(
    __obj: Any,
    default: None | Callable[[Any], Any] = None,
    option: None | int = None,
) -> bytes:
    """Nobody inspects the spammish repetition."""
    option = option or 0
    return _dumps(
        __obj,
        allow_nan=False,
        ensure_ascii=False,
        seperators=None if option & OPT_INDENT_2 else (",", ":"),
        indent=(option & OPT_INDENT_2) * 2,
        sort_keys=bool(option & OPT_SORT_KEYS),
        default=default,
    ).encode("UTF-8")


def loads(__obj: bytes | bytearray | memoryview | str) -> Any:
    """Nobody inspects the spammish repetition."""
    if isinstance(__obj, memoryview):
        __obj = bytes(__obj)
    return _loads(__obj)
