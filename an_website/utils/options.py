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

"""Options in this module are configurable when accessing the website."""

from __future__ import annotations

import dataclasses
from abc import ABC
from collections.abc import Callable, Iterable
from functools import partial
from typing import Generic, Literal, TypeVar, overload

from tornado.web import RequestHandler

from .utils import (
    THEMES,
    BumpscosityValue,
    OpenMojiValue,
    bool_to_str,
    parse_bumpscosity,
    parse_openmoji_arg,
    str_to_bool,
)

T = TypeVar("T")
U = TypeVar("U")


@dataclasses.dataclass(frozen=True)
class Option(ABC, Generic[T]):
    """An option that can be configured when accessing the website."""

    name: str
    parse_from_string: Callable[[str, T], T]
    get_default_value: Callable[[RequestHandler], T]
    is_valid: Callable[[T], bool] = lambda _: True
    normalize_string: Callable[[str], str] = lambda value: value
    value_to_string: Callable[[T], str] = str

    @overload
    def __get__(  # noqa: D105
        self, obj: None, _: type[Options] | None = None, /  # noqa: W504
    ) -> Option[T]:
        ...

    @overload
    def __get__(self, obj: Options, _: type[Options] | None = None, /) -> T:
        """Get the value for this option."""

    def __get__(
        self,  # comment to make Flake8 happy
        obj: Options | None,
        _: type[Options] | None = None,
        /,
    ) -> T | Option[T]:
        """Get the value for this option."""
        if obj is None:
            return self
        return self.get_value(obj.request_handler)

    def __set__(self, obj: RequestHandler, value: object) -> None:
        """Make this read-only."""
        raise AttributeError()

    def get_form_appendix(self, request_handler: RequestHandler) -> str:
        """Return the form appendix for this option."""
        if not self.option_in_arguments(request_handler):
            return ""
        return (
            f"<input class='hidden' name={self.name!r} "
            f"value={self.value_to_string(self.get_value(request_handler))!r}>"
        )

    def get_value(
        self,
        request_handler: RequestHandler,
        *,
        include_argument: bool = True,
        include_cookie: bool = True,
    ) -> T:
        """Get the value for this option."""
        return self.parse(
            argument=request_handler.get_argument(self.name, None)
            if include_argument
            else None,
            cookie=request_handler.get_cookie(self.name, None)
            if include_cookie
            else None,
            default=self.get_default_value(request_handler),
        )

    def option_in_arguments(self, request_handler: RequestHandler) -> bool:
        """Return whether the option is taken from the arguments."""
        return self.get_value(
            request_handler, include_argument=False
        ) != self.get_value(request_handler)

    def parse(
        self, *, argument: str | None, cookie: str | None, default: T
    ) -> T:
        """Parse the value from a string."""
        for val in (argument, cookie):
            if not val:
                continue
            parsed = self.parse_from_string(self.normalize_string(val), default)
            # is True to catch the case where is_valid returns NotImplemented
            if self.is_valid(parsed) is True:
                return parsed
        return default


def parse_int(value: str, default: int) -> int:
    """Parse the value from a string."""
    try:
        return int(value, base=0)
    except ValueError:
        return default


def parse_string(value: str, _: str) -> str:
    """Parse the value from a string."""
    return value


StringOption = partial(Option[str], parse_from_string=parse_string)
BoolOption = partial(
    Option[bool], parse_from_string=str_to_bool, value_to_string=bool_to_str
)
IntOption = partial(Option[int], parse_from_string=parse_int)


def false(_: RequestHandler) -> Literal[False]:
    """Return False."""
    return False


def true(_: RequestHandler) -> Literal[True]:
    """Return True."""
    return True


class Options:
    """Options for the website."""

    __slots__ = ("__request_handler",)

    theme: Option[str] = StringOption(
        name="theme",
        is_valid=THEMES.__contains__,
        get_default_value=lambda _: "default",
        normalize_string=lambda s: s.replace("-", "_").lower(),
    )
    compat: Option[bool] = BoolOption(name="compat", get_default_value=false)
    dynload: Option[bool] = BoolOption(name="dynload", get_default_value=false)
    effects: Option[bool] = BoolOption(name="effects", get_default_value=true)
    openmoji: Option[OpenMojiValue] = Option(
        name="openmoji",
        parse_from_string=parse_openmoji_arg,
        get_default_value=false,
    )
    no_3rd_party: Option[bool] = BoolOption(
        name="no_3rd_party",
        get_default_value=lambda handler: handler.request.host_name.endswith(
            (".onion", ".i2p")
        ),
    )
    bumpscosity: Option[BumpscosityValue] = Option(
        name="bumpscosity",
        get_default_value=lambda _: parse_bumpscosity(None),
        parse_from_string=lambda v, u: parse_bumpscosity(v),
    )

    def __init__(self, request_handler: RequestHandler) -> None:
        """Initialize the options."""
        self.__request_handler = request_handler

    def as_dict(
        self, *, include_argument: bool = True, include_cookie: bool = True
    ) -> dict[str, object]:
        """Get all the options in a dictionary."""
        return {
            option.name: option.get_value(
                self.request_handler,
                include_argument=include_argument,
                include_cookie=include_cookie,
            )
            for option in self.iter_options()
        }

    def as_dict_with_str_values(
        self, *, include_argument: bool = True, include_cookie: bool = True
    ) -> dict[str, str]:
        """Get all the options in a dictionary."""
        return {
            option.name: option.value_to_string(
                option.get_value(
                    self.request_handler,
                    include_argument=include_argument,
                    include_cookie=include_cookie,
                )
            )
            for option in self.iter_options()
        }

    def get_form_appendix(self) -> str:
        """Get HTML to add to forms to keep important query args."""
        return "".join(
            option.get_form_appendix(self.request_handler)
            for option in self.iter_options()
        )

    def iter_option_names(self) -> Iterable[str]:
        """Get the names of all options."""
        for option in self.iter_options():
            yield option.name

    def iter_options(self) -> Iterable[Option[object]]:
        """Get all the options."""
        for name in dir(self):
            if name.startswith("_"):
                continue
            value = getattr(self.__class__, name)
            if isinstance(value, Option):
                yield value

    @property
    def request_handler(self) -> RequestHandler:
        """Return the request handler."""
        return self.__request_handler
