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
from collections.abc import Set
from dataclasses import asdict, dataclass, field
from typing import Final

import regex
from tornado.web import HTTPError

from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, length_of_match, n_from_set
from . import FILE_NAMES, LANGUAGES, get_letters, get_words

WILDCARDS_REGEX: Final = regex.compile(r"[*_?-]+")
WORD_CHARS: Final = "a-zA-ZäöüßÄÖÜẞ"
NOT_WORD_CHAR: Final = regex.compile(rf"[^{WORD_CHARS}]+")
NOT_WORD_CHAR_OR_WILDCARD: Final = regex.compile(rf"[^_{WORD_CHARS}]")


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
    words: Set[str] = field(default_factory=frozenset)
    word_count: int = 0
    letters: dict[str, int] = field(default_factory=dict)
    crossword_mode: bool = False
    max_words: int = 20
    lang: str = "de_only_a-z"


def fix_input_str(_input: str) -> str:
    """Make the input lower case, strips it and replace wildcards with _."""
    wild_cards_normalized = WILDCARDS_REGEX.sub(
        lambda m: "_" * length_of_match(m), _input.lower().strip()
    )[:100]
    return NOT_WORD_CHAR_OR_WILDCARD.sub("", wild_cards_normalized)


def fix_invalid(invalid: str) -> str:
    """Replace chars that aren't word chars and remove duplicate chars."""
    return NOT_WORD_CHAR.sub(
        "", "".join(set(invalid.lower()))
    )  # replace stuff that could be bad


def generate_pattern_str(
    input_str: str, invalid: str, crossword_mode: bool
) -> str:
    """Generate a pattern string that matches a word."""
    input_str = input_str.lower()

    # in crossword_mode it doesn't matter
    # if the letters are already in input_str
    if not crossword_mode:
        # add if not cw_mode
        invalid += input_str

    invalid_chars = fix_invalid(invalid)

    if not invalid_chars:
        # there are no invalid chars,
        # so the wildcard can be replaced with just "."
        return WILDCARDS_REGEX.sub(
            lambda m: "." * length_of_match(m), input_str
        )

    wild_card_replacement = "[^" + invalid_chars + "]"

    return WILDCARDS_REGEX.sub(
        lambda m: (wild_card_replacement + "{" + str(length_of_match(m)) + "}"),
        input_str,
    )


def fix_letter_counter_crossword_mode(
    letter_counter: Counter[str], input_letters: str, matched_words_count: int
) -> None:
    """Fix the letter count for crossword mode."""
    n_word_count = -1 * matched_words_count
    update_dict: dict[str, int] = {}
    for key, value in Counter(input_letters).most_common(30):
        update_dict[key] = n_word_count * value
    letter_counter.update(update_dict)


def filter_words(
    words: Set[str] | str,
    pattern: regex.Pattern[str],
    input_letters: str,
    crossword_mode: bool = False,
    matches_always: bool = False,
) -> tuple[set[str], dict[str, int]]:
    """Filter a set of words to get only those that match the regex."""
    # if "words" is string it is a filename
    if isinstance(words, str):
        words = get_words(words)

    matched_words: set[str] = set()
    letter_list: list[str] = []
    for line in words:
        if matches_always or pattern.fullmatch(line) is not None:
            matched_words.add(line)

            # add letters to list
            if crossword_mode:
                letter_list.extend(line)
            else:
                # add every letter only once
                letter_list.extend(set(line))

    # count letters
    letter_counter = Counter(letter_list)

    # fix count for crossword_mode
    if crossword_mode:
        fix_letter_counter_crossword_mode(
            letter_counter,
            input_letters,
            len(matched_words),
        )

    # put letters in sorted dict
    sorted_letters: dict[str, int] = dict(
        letter_counter.most_common(30)
    )  # 26 + äöüß

    if not crossword_mode:
        # remove letters that are already in input
        for letter in set(input_letters.lower()):
            if letter in sorted_letters:
                del sorted_letters[letter]

    return matched_words, sorted_letters


def get_words_and_letters(
    filename: str,
    input_str: str,
    invalid: str,
    crossword_mode: bool,
) -> tuple[Set[str], dict[str, int]]:
    """Generate a word set and a letters dict and return them in a tuple."""
    input_letters: str = WILDCARDS_REGEX.sub("", input_str)
    matches_always = not invalid and not input_letters

    if matches_always and not crossword_mode:
        return get_words(filename), get_letters(filename)

    pattern = generate_pattern_str(input_str, invalid, crossword_mode)

    return filter_words(
        filename,
        regex.compile(pattern, regex.ASCII),
        input_letters,
        crossword_mode,
        matches_always,
    )


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
    invalid = fix_invalid(invalid)

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

    # do the solving
    matched_words, letters = get_words_and_letters(
        filename, input_str, invalid, crossword_mode
    )

    return Hangman(
        input_str,
        invalid,
        n_from_set(matched_words, max_words),
        len(matched_words),
        letters,
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
        await self.render("pages/hangman_solver.html", **asdict(hangman))


class HangmanSolverAPI(APIRequestHandler, HangmanSolver):
    """Request handler for the hangman solver API."""

    RATELIMIT_GET_LIMIT = 10

    @parse_args(type_=HangmanArguments, name="data")
    async def get(self, *, data: HangmanArguments, head: bool = False) -> None:
        """Handle GET requests to the hangman solver API."""
        if head:
            return
        hangman = solve_hangman(data)
        hangman_dict = asdict(hangman)
        # convert set to list, because the set can't be converted to JSON
        hangman_dict["words"] = list(hangman_dict["words"])
        await self.finish(hangman_dict)
