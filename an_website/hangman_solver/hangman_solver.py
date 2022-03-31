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

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from functools import lru_cache

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, length_of_match, n_from_set, str_to_bool
from . import FILE_NAMES, LANGUAGES, get_letters, get_words

WILDCARDS_REGEX = re.compile(r"[_?-]+")
NOT_WORD_CHAR = re.compile(r"[^a-zA-ZäöüßÄÖÜẞ]+")


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/hangman-loeser", HangmanSolver),
            (r"/api/hangman-loeser", HangmanSolverAPI),
        ),
        name="Hangman-Löser",
        description="Ein Website, die Lösungen für Galgenmännchen findet",
        path="/hangman-loeser",
        keywords=("Galgenmännchen", "Hangman", "Löser", "Solver", "Worte"),
        aliases=(
            "/hangman-l%C3%B6ser",
            "/hangman-löser",
            "/hangman-solver",
        ),
    )


@dataclass()
class Hangman:  # pylint: disable=too-many-instance-attributes
    """Hangman object that holds all the important information."""

    input: str = ""
    invalid: str = ""
    words: frozenset[str] = field(default_factory=frozenset)
    word_count: int = 0
    letters: dict[str, int] = field(default_factory=dict)
    crossword_mode: bool = False
    max_words: int = 20
    lang: str = "de_only_a-z"


def fix_input_str(_input: str) -> str:
    """Make the input lower case, strips it and replace wildcards with _."""
    return WILDCARDS_REGEX.sub(
        lambda m: "_" * length_of_match(m), _input.lower().strip()
    )[:100]


def fix_invalid(invalid: str) -> str:
    """Replace chars that aren't word chars and remove duplicate chars."""
    return NOT_WORD_CHAR.sub(
        "", "".join(set(invalid.lower()))
    )  # replace stuff that could be bad


async def generate_pattern_str(
    input_str: str, invalid: str, crossword_mode: bool
) -> str:
    """Generate a pattern string that matches a word."""
    input_str = input_str.lower()

    # in crossword_mode it doesn't matter
    # if the letters are already in input_str:
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


@lru_cache(5)
def filter_words(
    words: frozenset[str] | str,
    regex: re.Pattern[str],
    input_letters: str,
    crossword_mode: bool = False,
    matches_always: bool = False,
) -> tuple[frozenset[str], dict[str, int]]:
    """Filter a set of words to get only those that match the regex."""
    # if "words" is string it is a file_name
    if isinstance(words, str):
        words = get_words(words)

    matched_words: set[str] = set()
    letter_list: list[str] = []
    for line in words:
        if matches_always or regex.fullmatch(line) is not None:
            matched_words.add(line)

            # add letters to list
            if crossword_mode:
                letter_list.extend(line)
            else:
                # add every letter only once
                letter_list.extend(set(line))

    # count letters:
    letter_counter = Counter(letter_list)

    # fix count for crossword_mode:
    if crossword_mode:
        fix_letter_counter_crossword_mode(
            letter_counter,
            input_letters,
            len(matched_words),
        )

    # put letters in sorted dict:
    sorted_letters: dict[str, int] = dict(
        letter_counter.most_common(30)
    )  # 26 + äöüß

    if not crossword_mode:
        # remove letters that are already in input
        for letter in set(input_letters.lower()):
            if letter in sorted_letters:
                del sorted_letters[letter]

    return frozenset(matched_words), sorted_letters


async def get_words_and_letters(
    file_name: str,
    input_str: str,
    invalid: str,
    crossword_mode: bool,
) -> tuple[frozenset[str], dict[str, int]]:
    """Generate a word set and a letters dict and return them in a tuple."""
    input_letters: str = WILDCARDS_REGEX.sub("", input_str)
    matches_always = not invalid and not input_letters

    if matches_always and not crossword_mode:
        return get_words(file_name), get_letters(file_name)

    pattern = await generate_pattern_str(input_str, invalid, crossword_mode)

    return filter_words(
        file_name,
        re.compile(pattern, re.ASCII),
        input_letters,
        crossword_mode,
        matches_always,
    )


async def solve_hangman(
    input_str: str,
    invalid: str,
    language: str,
    max_words: int,
    crossword_mode: bool,
) -> Hangman:
    """Generate a hangman object based on the input and return it."""
    if language not in LANGUAGES:
        raise HTTPError(400, reason=f"'{language}' is an invalid language")

    input_str = fix_input_str(input_str)
    invalid = fix_invalid(invalid)

    input_len = len(input_str)

    # to be short (is only the key of the words dict in __init__.py)
    file_name = f"words_{language}/{input_len}"

    if file_name not in FILE_NAMES:
        # no words with the length
        return Hangman(
            input=input_str,
            invalid=invalid,
            crossword_mode=crossword_mode,
            max_words=max_words,
            lang=language,
        )

    # do the solving:
    matched_words, letters = await get_words_and_letters(
        file_name, input_str, invalid, crossword_mode
    )

    return Hangman(
        input_str,
        invalid,
        frozenset(n_from_set(matched_words, max_words)),
        len(matched_words),
        letters,
        crossword_mode,
        max_words,
        language,
    )


class HangmanSolver(HTMLRequestHandler):
    """Request handler for the hangman solver page."""

    RATELIMIT_GET_LIMIT = 10

    async def get_hangman_obj(self) -> Hangman:
        """Get the information and return the Hangman object."""
        max_words = max(
            0,
            min(
                100,
                int(str(self.get_query_argument("max_words", default="20"))),
            ),
        )

        crossword_mode_str = str(
            self.get_query_argument("crossword_mode", default="False")
        )
        crossword_mode = str_to_bool(crossword_mode_str)  # if crossword mode

        language = str(self.get_query_argument("lang", default="de_only_a-z"))

        input_str = str(self.get_query_argument("input", default=""))

        invalid = str(self.get_query_argument("invalid", default=""))

        return await solve_hangman(
            max_words=max_words,
            crossword_mode=crossword_mode,
            language=language,
            input_str=input_str,
            invalid=invalid,
        )

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request and render the page."""
        if head:
            return
        hangman = await self.get_hangman_obj()
        await self.render("pages/hangman_solver.html", **asdict(hangman))


class HangmanSolverAPI(HangmanSolver, APIRequestHandler):
    """Request handler for the hangman solver JSON API."""

    RATELIMIT_GET_LIMIT = 10
    IS_NOT_HTML = True

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request and write the Hangman object as JSON."""
        if head:
            return
        hangman = await self.get_hangman_obj()
        hangman_dict = asdict(hangman)
        # convert set to list, because the set can't be converted to JSON.
        hangman_dict["words"] = list(hangman_dict["words"])
        return await self.finish(hangman_dict)


# def profile():
#     import cProfile
#     import pstats
#
#     with cProfile.Profile() as pr:
#         cache_words_and_letters_in_pickles()
#         # filter_words(
#         #     words="words_de/20",
#         #     regex=re.compile("[^en]{19}en"),
#         #     input_letters="en"
#         # )
#     stats = pstats.Stats(pr)
#     stats.sort_stats(pstats.SortKey.TIME)
#     stats.print_stats()
#     stats.dump_stats(filename="profiling.prof")
