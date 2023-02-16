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

"""A page that helps solving hangman puzzles."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Set
from dataclasses import dataclass
from operator import itemgetter
from typing import Any, Final

from tornado.web import HTTPError
from typed_stream import Stream

from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo
from . import FILE_NAMES, LANGUAGES, get_letters, get_words

import regex

WILDCARD_CHARS: Final = b"_?-"
WHITE_SPACES: Final = regex.compile(r"\s+")


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/hangman-loeser", HangmanSolver),
            (r"/api/hangman-loeser", HangmanSolverAPI),
        ),
        name="Hangman-Löser",
        description="Eine Webseite, die Lösungen für Galgenmännchen findet",
        path="/hangman-loeser",
        keywords=("Galgenmännchen", "Hangman", "Löser", "Solver", "Worte"),
        aliases=(
            "/hangman-l%C3%B6ser",
            "/hangman-löser",
            "/hangman-solver",
        ),
    )


@dataclass(slots=True)
class Hangman:  # pylint: disable=too-many-instance-attributes
    """Hangman object that holds all the important information."""

    input: str = ""
    invalid: str = ""
    words: Iterable[bytes] = ()
    word_count: int = 0
    letters: Mapping[int, int] | None = None
    crossword_mode: bool = False
    max_words: int = 20
    lang: str = "de_only_a-z"

    def to_dict(self, for_json: bool = False) -> dict[str, Any]:
        """Return as a normalized dictionary representation."""
        data = {
            "input": self.input.replace("?", "_").replace("-", "_"),
            "invalid": Stream(self.invalid).distinct().collect("".join),
            "words": [word.decode("CP1252") for word in self.words],
            "word_count": self.word_count,
            "crossword_mode": self.crossword_mode,
            "max_words": self.max_words,
            "lang": self.lang,
        }
        if self.letters or not for_json:
            data["letters"] = {
                bytes((byte,)).decode("CP1252"): count
                for byte, count in self.letters.items()
            } if self.letters else {}
        return data


def fix_input_str(input_: str) -> str:
    """Make the input lower case and remove whitespaces."""
    return WHITE_SPACES.sub("", input_.lower())


def create_words_filter(
    input_str: str, invalid: str, crossword_mode: bool
) -> WordsFilter:
    """Generate a pattern string that matches a word."""
    input_str = input_str.lower()

    # in crossword_mode it doesn't matter
    # if the letters are already in input_str
    if not crossword_mode:
        # add if not cw_mode
        invalid += input_str

    return WordsFilter(fix_input_str(input_str).encode("CP1252"), fix_input_str(invalid).encode("CP1252"))


class WordsFilter:
    """Class to filter words based on a simple pattern."""

    filters: Final[tuple[Callable[[int], bool], ...]]
    first_letter: Final[int | None]
    __slots__ = "filters", "first_letter"

    def __init__(self, pattern: bytes, invalid_letters: bytes) -> None:
        invalid_letters_tpl = tuple(
            idx in invalid_letters
            for idx in range(256)
        )
        self.first_letter = None if pattern[0] in WILDCARD_CHARS else pattern[0]
        self.filters = tuple(
            (
                invalid_letters_tpl.__getitem__
                if letter in WILDCARD_CHARS
                else letter.__ne__
            )
            for letter in pattern
        )

    def matches(self, word: bytes) -> bool:
        for fun, letter in zip(self.filters, word, strict=True):
            if fun(letter):
                return False
        return True

    def pre_filter(self, words: Stream[bytes]) -> Stream[bytes]:
        if self.first_letter is None:
            return words
        first_letter = self.first_letter
        return words.drop_while(lambda w: w[0] != first_letter).take_while(
            lambda w: w[0] == first_letter
        )


def filter_words(
    words_path: str,
    words_filter: WordsFilter | None,
) -> Stream[bytes]:
    """Filter a set of words to get only those that match the regex."""
    stream = get_words(words_path)
    return (
        words_filter.pre_filter(stream).filter(words_filter.matches)
        if words_filter
        else stream
    )


def get_letters_from_words(
    words: Iterable[bytes], input_letters: bytes
) -> Mapping[int, int]:
    """Get a letters dictionary from words."""
    stream: Stream[int] = Stream(words).flat_map(set)
    return Counter(stream.exclude(input_letters.__contains__))


def get_words_and_letters(
    filename: str,
    input_str: str,
    invalid: str,
) -> tuple[tuple[bytes, ...], Mapping[int, int]]:
    """Generate a word set and a letters dict and return them in a tuple."""
    input_letters: str = fix_input_str(input_str)
    matches_always = not invalid and not input_letters

    if matches_always:
        return tuple(get_words(filename)), get_letters(filename)

    words = filter_words(
        filename,
        None
        if matches_always
        else create_words_filter(input_str, invalid, False),
    ).collect(tuple)
    return words, get_letters_from_words(words, input_letters.encode("CP1252"))


@dataclass(slots=True)
class HangmanArguments:
    """Arguments for the hangman solver."""

    max_words: int = 20
    crossword_mode: bool = False
    lang: str = "de_only_a-z"
    input: str = ""
    invalid: str = ""


def solve_hangman(data: HangmanArguments) -> Hangman:
    """Generate a hangman object based on the input and return it."""
    return _solve_hangman(
        max_words=max(20, min(100, data.max_words)),
        crossword_mode=data.crossword_mode,
        language=data.lang,
        input_str=data.input,
        invalid=data.invalid,
    )


def _solve_hangman(
    input_str: str,
    invalid: str,
    language: str,
    max_words: int,
    crossword_mode: bool,
) -> Hangman:
    """Generate a hangman object based on the input and return it."""
    if language not in LANGUAGES:
        raise HTTPError(400, reason=f"{language!r} is an invalid language")

    input_str = fix_input_str(input_str)
    invalid = fix_input_str(invalid)

    input_len = len(input_str)

    # to be short (is only the key of the words dict in __init__.py)
    filename = f"{language}/{input_len}"

    if filename not in FILE_NAMES:
        # no words with the length
        return Hangman(
            input=input_str,
            invalid=invalid,
            crossword_mode=crossword_mode,
            max_words=max_words,
            lang=language,
        )
    if crossword_mode:
        matched_words = tuple(
            filter_words(
                filename, create_words_filter(input_str, invalid, True)
            )
        )
        letters = None
        found_words_count = len(matched_words)
    else:
        # do the solving
        matched_words, letters = get_words_and_letters(
            filename, input_str, invalid
        )
        found_words_count = len(matched_words)

    return Hangman(
        input_str,
        invalid,
        matched_words[:max_words],
        found_words_count,
        dict(sorted(letters.items(), key=itemgetter(1), reverse=True))
        if letters is not None
        else None,
        crossword_mode,
        max_words,
        language,
    )


class HangmanSolver(HTMLRequestHandler):
    """Request handler for the hangman solver page."""

    RATELIMIT_GET_LIMIT = 10

    @parse_args(type_=HangmanArguments, name="data")
    async def get(self, *, data: HangmanArguments, head: bool = False) -> None:
        """Handle GET requests to the hangman solver page."""
        if head:
            return
        hangman = solve_hangman(data)
        await self.render("pages/hangman_solver.html", **hangman.to_dict())


class HangmanSolverAPI(APIRequestHandler, HangmanSolver):
    """Request handler for the hangman solver API."""

    RATELIMIT_GET_LIMIT = 10
    IS_NOT_HTML = True

    @parse_args(type_=HangmanArguments, name="data")
    async def get(self, *, data: HangmanArguments, head: bool = False) -> None:
        """Handle GET requests to the hangman solver API."""
        if head:
            return
        await self.finish(solve_hangman(data).to_dict(True))
