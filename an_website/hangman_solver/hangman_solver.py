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

from dataclasses import dataclass

from hangman_solver import (
    HangmanResult,
    Language,
    UnknownLanguageError,
    read_words_with_length,
    solve,
    solve_crossword,
)
from tornado.web import HTTPError

from ..utils.base_request_handler import BaseRequestHandler
from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    languages = "|".join([lang.value.lower() for lang in Language.values()])
    return ModuleInfo(
        handlers=(
            (r"/hangman-loeser", HangmanSolver),
            (r"/api/hangman-loeser", HangmanSolverAPI),
            (
                rf"/hangman-loeser/worte/({languages})/([1-9]\d*).txt",
                HangmanSolverWords,
            ),
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
class HangmanArguments:
    """Arguments for the hangman solver."""

    max_words: int = 20
    crossword_mode: bool = False
    lang: str = "de"
    input: str = ""
    invalid: str = ""

    def get_max_words(self) -> int:
        """Return the maximum number of words."""
        return max(0, min(100, self.max_words))


def solve_hangman(data: HangmanArguments) -> HangmanResult:
    """Generate a hangman object based on the input and return it."""
    try:
        lang = Language.parse_string(data.lang)
    except UnknownLanguageError as err:
        raise HTTPError(
            400, reason=f"{data.lang!r} is an invalid language"
        ) from err

    return (solve_crossword if data.crossword_mode else solve)(
        data.input, data.invalid, lang, data.get_max_words()
    )


class HangmanSolver(HTMLRequestHandler):
    """Request handler for the hangman solver page."""

    RATELIMIT_GET_LIMIT = 10

    @parse_args(type_=HangmanArguments, name="data")
    async def get(self, *, data: HangmanArguments, head: bool = False) -> None:
        """Handle GET requests to the hangman solver page."""
        if head:
            return

        await self.render(
            "pages/hangman_solver.html",
            hangman_result=solve_hangman(data),
            data=data,
        )


class HangmanSolverAPI(APIRequestHandler, HangmanSolver):
    """Request handler for the hangman solver API."""

    RATELIMIT_GET_LIMIT = 10

    @parse_args(type_=HangmanArguments, name="data")
    async def get(self, *, data: HangmanArguments, head: bool = False) -> None:
        """Handle GET requests to the hangman solver API."""
        if head:
            return
        hangman_result = solve_hangman(data)
        await self.finish(
            {
                "input": hangman_result.input,
                "invalid": "".join(hangman_result.invalid),
                "words": hangman_result.words,
                "word_count": hangman_result.matching_words_count,
                "letters": dict(hangman_result.letter_frequency),
                "crossword_mode": data.crossword_mode,
                "max_words": data.get_max_words(),
                "lang": hangman_result.language.value,
            }
        )


class HangmanSolverWords(BaseRequestHandler):
    """Request handler for the hangman word lists."""

    RATELIMIT_GET_LIMIT = 15
    POSSIBLE_CONTENT_TYPES = ("text/plain",)

    async def get(
        self, language: str, length: str, *, head: bool = False
    ) -> None:
        """Handle GET requests to the hangman solver page."""
        # pylint: disable=unused-argument
        try:
            lang = Language.parse_string(language)
        except UnknownLanguageError as err:
            raise HTTPError(404) from err

        try:
            word_length = int(length)
        except ValueError as err:
            raise HTTPError(404) from err

        for word in read_words_with_length(lang, word_length):
            self.write(word)
            self.write(b"\n")

        await self.finish()
