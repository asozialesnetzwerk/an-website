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
from dataclasses import asdict, dataclass, field
from typing import Final

import regex
from hangman_solver import Language, solve, solve_crossword
from tornado.web import HTTPError

from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo

WILDCARDS_REGEX: Final = regex.compile(r"[*_?-]")


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


def fix_input_str(_input: str) -> str:
    """Make the input lower case, strips it and replace wildcards with _."""
    return WILDCARDS_REGEX.sub("_", _input.lower().strip())


def get_letter_freq_crossword_mode(
    words: list[str], input_letters: str
) -> dict[str, int]:
    """Get the letter frequency for crossword mode."""
    letter_counter: Counter[str] = Counter()
    for word in words:
        letter_counter.update(word)
    neg_matched_words_count = -len(words)
    update_dict: dict[str, int] = {
        key: neg_matched_words_count * val
        for key, val in Counter(input_letters.replace("_", "")).most_common(30)
    }
    letter_counter.update(update_dict)
    return {key: val for key, val in letter_counter.items() if val}


@dataclass(slots=True)
class Hangman:  # pylint: disable=too-many-instance-attributes
    """Hangman object that holds all the important information."""

    input: str = ""
    invalid: str = ""
    words: list[str] = field(default_factory=list)
    word_count: int = 0
    letters: dict[str, int] = field(default_factory=dict)
    crossword_mode: bool = False
    max_words: int = 20
    lang: str = "de"


@dataclass(slots=True)
class HangmanArguments:
    """Arguments for the hangman solver."""

    max_words: int = 20
    crossword_mode: bool = False
    lang: str = "de"
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
    try:
        lang = Language.parse_string(language)
    except ValueError as err:
        raise HTTPError(
            400, reason=f"{language!r} is an invalid language"
        ) from err

    # do the solving
    hangman = (solve_crossword if crossword_mode else solve)(
        fix_input_str(input_str), list(invalid), lang
    )

    letter_freq = (
        get_letter_freq_crossword_mode(hangman.words, hangman.input)
        if crossword_mode
        else hangman.letter_frequency()
    )

    return Hangman(
        hangman.input,
        "".join(hangman.invalid),
        hangman.words[:max_words],
        len(hangman.words),
        dict(sorted(letter_freq.items(), key=lambda x: (-x[1], x[0]))),
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
