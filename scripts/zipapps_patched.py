#!/usr/bin/env python3

"""Run zipapps with customized compression."""

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

import builtins
import contextlib
import os
import time
import zipfile
from collections.abc import Iterable, Iterator, MutableSet, Set
from pathlib import Path
from typing import Literal, Self

import time_machine
import zopfli
from zipapps.__main__ import main  # type: ignore[import-untyped]

DO_NOT_COMPRESS = (
    "an_website/static/",
    "an_website/soundboard/files/",
    "an_website/vendored/apm-rum/",
    "openmoji_dist/openmoji/",
)
EPOCH: int = 512 * 83 * 27 * 25 * 11
EPOCH_TUPLE = time.gmtime(EPOCH)[:6]


class OrderedSet[T](MutableSet[T]):
    """An ordered set."""

    value: list[T]

    def __contains__(self, value: object) -> bool:
        """Contains."""
        return value in self.value

    def __iand__(self, it: object, /) -> Self:
        """Idk."""
        raise NotImplementedError()

    def __init__(self, iterable: Iterable[T] = ()):
        """Init self."""
        self.value = []
        self.update(iterable)

    def __ior__(self, it: object, /) -> Self:
        """Update."""
        if isinstance(it, Set):
            self.update(it)
            return self
        return NotImplemented

    def __isub__(self, it: object, /) -> Self:
        """Minus."""
        if isinstance(it, Set):
            for value in it:
                self.discard(value)
            return self
        return NotImplemented

    def __iter__(self) -> Iterator[T]:
        """Iterate."""
        with contextlib.suppress(Exception):
            self.value.sort()
        return iter(self.value)

    def __ixor__(self, it: object, /) -> Self:
        """Idk."""
        raise NotImplementedError()

    def __len__(self) -> int:
        """Length."""
        return len(self.value)

    def add(self, value: T, /) -> None:
        """Add an element."""
        if value not in self.value:
            self.value.append(value)

    def clear(self) -> None:
        """Glass."""
        self.value.clear()

    def difference(self, values: Iterable[T]) -> Self:
        """Minus."""
        copy: Self = type(self)(self)
        for value in values:
            copy.discard(value)
        return copy

    def discard(self, value: T, /) -> None:
        """Remove an element.  Do not raise an exception if absent."""
        try:
            self.value.remove(value)
        except ValueError:
            ...

    def pop(self) -> T:
        """Return the popped value.  Raise KeyError if empty."""
        try:
            return self.value.pop()
        except IndexError as err:
            raise KeyError() from err

    def remove(self, value: T, /) -> None:
        """Remove an element. If not a member, raise a KeyError."""
        try:
            self.value.remove(value)
        except ValueError as err:
            raise KeyError() from err

    def update(self, values: Iterable[T]) -> None:
        """Update."""
        for value in values:
            self.add(value)


class ZipFile(zopfli.ZipFile):
    """ZipFile with custom compression logic."""

    def write(
        self,
        filename: str | os.PathLike[str],
        arcname: str | os.PathLike[str] | None = None,
        compress_type: int | None = None,
        compresslevel: int | None = None,
        **kwargs: object,
    ) -> None:
        """Write with custom compression logic."""
        # assert current calling behaviour of zipapp.py
        assert self.compression == zipfile.ZIP_STORED
        assert not kwargs
        assert compress_type is None
        assert compresslevel is None
        assert arcname is not None
        assert isinstance(arcname, str)

        writestr_kwargs: dict[Literal["compress_type", "compresslevel"], int]

        if arcname.startswith(DO_NOT_COMPRESS):
            writestr_kwargs = {}
        elif arcname.endswith(".py"):
            writestr_kwargs = {
                "compress_type": zipfile.ZIP_DEFLATED,
            }
        else:
            writestr_kwargs = {
                "compress_type": zipfile.ZIP_ZSTANDARD,
                "compresslevel": 22,
            }

        path = Path(filename)

        if path.is_dir():
            return super().mkdir(arcname)

        return self.writestr(
            zipfile.ZipInfo(arcname, date_time=EPOCH_TUPLE),
            path.read_bytes(),
            **writestr_kwargs,
        )


if __name__ == "__main__":
    _set = builtins.set
    _Zip = zipfile.ZipFile
    try:
        builtins.set = OrderedSet  # type: ignore[assignment, misc]
        zipfile.ZipFile = ZipFile  # type: ignore[assignment, misc]

        with time_machine.travel(EPOCH, tick=False):
            main()
    finally:
        builtins.set = _set  # type: ignore[misc]
        zipfile.ZipFile = _Zip  # type: ignore[misc]
