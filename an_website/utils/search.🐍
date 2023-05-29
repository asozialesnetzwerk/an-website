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

"""Module used for easy and simple searching in O(n) complexity."""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Generic, NoReturn, TypeVar

import regex as re
from typed_stream import Stream

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class Query:
    """Class representing a query."""

    _data: tuple[str, Sequence[str], int]
    __slots__ = ("_data",)

    def __bool__(self) -> bool:
        """Return False if this query matches everything."""
        return bool(self.words)

    def __hash__(self) -> int:
        """Hash this."""
        return hash(self.query)

    def __init__(self, query: str) -> None:
        """Initialize this."""
        if hasattr(self, "_data"):
            raise ValueError("Already initialized.")
        query = query.lower()
        # pylint: disable=bad-builtin
        words = tuple(filter(None, re.split(r"\W+", query)))
        words_len = sum(len(word) for word in words)
        object.__setattr__(self, "_data", (query, words, words_len))

    def __reduce__(self) -> tuple[type[Query], tuple[str]]:
        """Reduce this object."""
        return Query, (self.query,)

    def __repr__(self) -> str:
        """Return a string representation of self."""
        return f"Query({self.query!r})"

    def __setattr__(self, key: object, value: object) -> NoReturn:
        """Raise an AttributeError."""
        raise AttributeError("Cannot modify Query.")

    @property
    def query(self) -> str:
        """The original query."""
        return self._data[0]

    def score(self, field_values: tuple[str, ...]) -> float:
        """Field values needs to be a tuple of lower cased strings."""
        if any(self.query in val for val in field_values):
            return 1.0
        return sum(
            (
                sum(word in value for value in field_values)
                * (len(word) / self.words_len)
            )
            for word in self.words
        ) / len(field_values)

    @property
    def words(self) -> Sequence[str]:
        """The words in the query."""
        return self._data[1]

    @property
    def words_len(self) -> int:
        """Return sum(len(word) for word in self.words)."""
        return self._data[2]


@dataclasses.dataclass(frozen=True, slots=True, order=True)
class ScoredValue(Generic[T]):
    """Value with score."""

    score: float
    value: T


class DataProvider(Generic[T, U]):
    """Provide Data."""

    __slots__ = ("_data", "_key", "_convert")

    _data: Iterable[T] | Callable[[], Iterable[T]]
    _key: Callable[[T], str | tuple[str, ...]]
    _convert: Callable[[T], U]

    def __init__(
        self,
        data: Iterable[T] | Callable[[], Iterable[T]],
        key: Callable[[T], str | tuple[str, ...]],
        convert: Callable[[T], U],
    ) -> None:
        """Initialize this."""
        self._data = data
        self._key = key
        self._convert = convert

    def _value_to_fields(self, value: T) -> tuple[str, ...]:
        """Convert a value to a tuple of strings."""
        return (
            (cpv.lower(),)
            if isinstance(cpv := self._key(value), str)
            else tuple(map(str.lower, cpv))  # pylint: disable=bad-builtin
        )

    @property
    def data(self) -> Iterable[T]:
        """Return the data."""
        return self._data if isinstance(self._data, Iterable) else self._data()

    def search(
        self, query: Query, excl_min_score: float = 0.0
    ) -> Iterator[ScoredValue[U]]:
        """Search this."""
        for value in self.data:
            score = query.score(self._value_to_fields(value))
            if score > excl_min_score:
                yield ScoredValue(score, self._convert(value))


def search(
    query: Query,
    *providers: DataProvider[object, T],
    excl_min_score: float = 0.0,
) -> list[ScoredValue[T]]:
    """Search through data."""
    return sorted(
        Stream(providers).flat_map(lambda x: x.search(query, excl_min_score)),
        key=lambda sv: sv.score,
    )
