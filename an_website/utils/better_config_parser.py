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

"""A config parser with the ability to parse command-line arguments."""
from __future__ import annotations

import argparse
import logging
import pathlib
from collections.abc import Callable, Iterable
from configparser import ConfigParser
from typing import Any, Final, TypeVar, cast, overload

from .utils import bool_to_str, get_arguments_without_help, str_to_set

LOGGER: Final = logging.getLogger(__name__)

T = TypeVar("T")
OptionalBool = TypeVar("OptionalBool", bool, None)
OptionalFloat = TypeVar("OptionalFloat", float, None)
OptionalInt = TypeVar("OptionalInt", int, None)
OptionalStr = TypeVar("OptionalStr", str, None)
OptionalSetStr = TypeVar("OptionalSetStr", set[str], None)


class BetterConfigParser(ConfigParser):
    """A better config parser."""

    _arg_parser: None | argparse.ArgumentParser
    _arg_parser_options_added: set[tuple[str, str]]
    _all_options_should_be_parsed: bool

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Initialize this config parser."""
        self._arg_parser_options_added = set()
        self._arg_parser = None
        self._all_options_should_be_parsed = False
        kwargs.setdefault("interpolation", None)
        kwargs["dict_type"] = dict
        super().__init__(*args, **kwargs)

    def _add_fallback_to_config(
        self,
        section: str,
        option: str,
        fallback: str | Iterable[str] | bool | int | float | None,
    ) -> None:
        if section in self and option in self[section]:
            return
        fallback = self._val_to_str(fallback)
        if fallback is None:
            fallback = ""
            option = f"#{option}"
        if section not in self.sections():
            self.add_section(section)
        self.set(section, option.lower(), fallback)

    def _get_conv(  # type: ignore[override]
        self, section: str, option: str, conv: Callable[[str], T], **kwargs: Any
    ) -> T | None:
        self._add_fallback_to_config(section, option, kwargs.get("fallback"))
        if (val := self._get_from_args(section, option, conv)) is not None:
            return val
        return cast(T, super()._get_conv(section, option, conv, **kwargs))

    def _get_from_args(
        self, section: str, option: str, conv: Callable[[str], T]
    ) -> None | T:
        """Try to get the value from the command line arguments."""
        if self._arg_parser is None:
            return None
        option_name = f"{section}-{option}".lower().removeprefix("general-")
        if (section, option) not in self._arg_parser_options_added:
            if self._all_options_should_be_parsed:
                LOGGER.error(
                    "Option %r in section %r should have been queried before.",
                    option,
                    section,
                )
            self._arg_parser.add_argument(
                f"--{option_name}".replace("_", "-"),
                required=False,
                type=conv,
                help=f"Override {option!r} in the {section!r} section of the config",
            )
            self._arg_parser_options_added.add((section, option))
        value = getattr(
            self._arg_parser.parse_known_args(get_arguments_without_help())[0],
            option_name.replace("-", "_"),
            None,
        )
        if value is None:
            return None
        self.set(section, option, self._val_to_str(value))
        return cast(T, value)

    def _val_to_str(self, value: object | None) -> str | None:
        """Convert a value to a string."""
        if value is None or isinstance(value, str):
            return value
        if isinstance(value, Iterable):
            return ", ".join(
                [cast(str, self._val_to_str(val)) for val in value]
            )
        if isinstance(value, bool):
            return bool_to_str(value)
        return str(value)  # float, int

    def add_override_argument_parser(
        self, parser: argparse.ArgumentParser
    ) -> None:
        """Add an argument parser to override config values."""
        self._arg_parser = parser

    @staticmethod
    def from_path(*path: pathlib.Path) -> BetterConfigParser:
        """Parse the config at the given path."""
        config = BetterConfigParser()
        config.read(path, encoding="UTF-8")
        return config

    @overload  # type: ignore[override]
    def get(  # noqa: D102  # pylint: disable=arguments-differ
        self, section: str, option: str, *, fallback: OptionalStr
    ) -> str | OptionalStr: ...

    @overload
    def get(  # pylint: disable=arguments-differ
        self, section: str, option: str
    ) -> str: ...

    def get(self, section: str, option: str, **kwargs: Any) -> object:
        """Get an option in a section."""
        self._add_fallback_to_config(section, option, kwargs.get("fallback"))
        if (val := self._get_from_args(section, option, str)) is not None:
            assert isinstance(val, str)
            return val
        return_value: str | None = super().get(section, option, **kwargs)
        if "fallback" in kwargs and kwargs["fallback"] is None:
            assert isinstance(return_value, (str, type(None)))
        else:
            assert isinstance(return_value, str)
        return return_value

    @overload  # type: ignore[override]
    def getboolean(  # noqa: D102  # pylint: disable=arguments-differ
        self, section: str, option: str, *, fallback: OptionalBool
    ) -> bool | OptionalBool: ...

    @overload
    def getboolean(  # pylint: disable=arguments-differ
        self, section: str, option: str
    ) -> bool: ...

    def getboolean(self, section: str, option: str, **kwargs: Any) -> object:
        """Get a boolean option."""
        return_value: bool | None = super().getboolean(
            section, option, **kwargs
        )
        if "fallback" in kwargs and kwargs["fallback"] is None:
            assert return_value in {False, None, True}
        else:
            assert return_value in {False, True}
        return return_value

    @overload  # type: ignore[override]
    def getfloat(  # noqa: D102  # pylint: disable=arguments-differ
        self, section: str, option: str, *, fallback: OptionalFloat
    ) -> float | OptionalFloat: ...

    @overload
    def getfloat(  # pylint: disable=arguments-differ
        self, section: str, option: str
    ) -> float: ...

    def getfloat(self, section: str, option: str, **kwargs: Any) -> object:
        """Get an int option."""
        return_value: float | None = super().getfloat(section, option, **kwargs)
        if "fallback" in kwargs and kwargs["fallback"] is None:
            assert isinstance(return_value, (float, type(None)))
        else:
            assert isinstance(return_value, float)
        return return_value

    @overload  # type: ignore[override]
    def getint(  # noqa: D102  # pylint: disable=arguments-differ
        self, section: str, option: str, *, fallback: OptionalInt
    ) -> int | OptionalInt: ...

    @overload
    def getint(  # pylint: disable=arguments-differ
        self, section: str, option: str
    ) -> int: ...

    def getint(self, section: str, option: str, **kwargs: Any) -> object:
        """Get an int option."""
        return_value: int | None = super().getint(section, option, **kwargs)
        if "fallback" in kwargs and kwargs["fallback"] is None:
            assert isinstance(return_value, (int, type(None)))
        else:
            assert isinstance(return_value, int)
        return return_value

    @overload
    def getset(  # noqa: D102
        self, section: str, option: str, *, fallback: OptionalSetStr
    ) -> set[str] | OptionalSetStr: ...

    @overload
    def getset(self, section: str, option: str) -> set[str]: ...

    def getset(self, section: str, option: str, **kwargs: Any) -> object:
        """Get an int option."""
        return_value: set[str] | None = self._get_conv(
            section, option, str_to_set, **kwargs
        )
        if "fallback" in kwargs and kwargs["fallback"] is None:
            assert isinstance(return_value, (set, type(None)))
        else:
            assert isinstance(return_value, set)
        if isinstance(return_value, set):
            assert all(isinstance(val, str) for val in return_value)
        return return_value

    def set_all_options_should_be_parsed(self) -> None:
        """Set all options should be parsed."""
        self._all_options_should_be_parsed = True
