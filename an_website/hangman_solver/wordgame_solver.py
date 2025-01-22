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

"""The module for the wordgame solver."""

from __future__ import annotations

from collections.abc import Collection

from hangman_solver import Language, read_words_with_length
from typed_stream import Stream

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, bounded_edit_distance


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/wortspiel-helfer", WordgameSolver),
            ("/api/wortspiel-helfer", WordgameSolverAPI),
        ),
        name="Wortspiel-Helfer",
        description=(
            "Findet Worte, die nur eine Änderung voneinander entfernt sind."
        ),
        path="/wortspiel-helfer",
        keywords=("Wortspiel", "Helfer", "Hilfe", "Worte"),
        aliases=("/wordgame-solver",),
        hidden=True,
    )


def find_solutions(word: str, ignore: Collection[str]) -> Stream[str]:
    """Find words that have only one different letter."""
    word_len = len(word)
    ignore = {*ignore, word}

    return (
        Stream((word_len - 1, word_len, word_len + 1))
        .flat_map(
            lambda length: read_words_with_length(
                Language.DeBasicUmlauts, length
            )
        )
        .exclude(ignore.__contains__)
        .filter(
            lambda test_word: bounded_edit_distance(word, test_word, 2) == 1
        )
    )


def get_ranked_solutions(
    word: str, before: Collection[str] = ()
) -> list[tuple[int, str]]:
    """Find solutions for the word and rank them."""
    if not word:
        return []
    before_with_word = {*before, word}
    return sorted(
        (
            (find_solutions(sol, before_with_word).count(), sol)
            for sol in find_solutions(word, before)
        ),
        reverse=True,
    )


class WordgameSolver(HTMLRequestHandler):
    """The request handler for the wordgame solver page."""

    RATELIMIT_GET_LIMIT = 10

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the wordgame solver page."""
        if head:
            return
        word = self.get_argument("word", "").lower()
        before_str = self.get_argument("before", "")
        before = [_w.strip() for _w in before_str.split(",") if _w.strip()]
        new_before = [*before, word] if word and word not in before else before

        await self.render(
            "pages/wordgame_solver.html",
            word=word,
            words=get_ranked_solutions(word, before),
            before=", ".join(before),
            new_before=", ".join(new_before),
        )


class WordgameSolverAPI(APIRequestHandler):
    """The request handler for the wordgame solver API."""

    RATELIMIT_GET_LIMIT = 10
    ALLOWED_METHODS = ("GET",)

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the wordgame solver API."""
        if head:
            return
        word: str = self.get_argument("word", "").lower()
        before_str: str = self.get_argument("before", "")
        before = [_w.strip() for _w in before_str.split(",") if _w.strip()]
        return await self.finish_dict(
            before=before,
            word=word,
            solutions=get_ranked_solutions(word, before),
        )
