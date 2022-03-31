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

from collections.abc import Iterable

from Levenshtein import distance  # type: ignore

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo
from . import FILE_NAMES, get_words


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/wortspiel-helfer", WordGameHelper),
            ("/api/wortspiel-helfer", WordGameHelperAPI),
        ),
        name="Wortspiel-Helfer",
        description=(
            "Findet Worte, die nur eine Änderung von einander entfernt sind."
        ),
        path="/wortspiel-helfer",
        keywords=("Wortspiel", "Helfer", "Hilfe", "Worte"),
        aliases=("/wordgame-solver",),
        hidden=True,
    )


async def find_solutions(
    word: str, ignore: Iterable[str] = tuple()
) -> set[str]:
    """Find words that have only one different letter."""
    solutions: set[str] = set()

    word_len = len(word)

    if not word_len:
        return solutions

    ignore = (*ignore, word)

    for sol_len in (word_len - 1, word_len, word_len + 1):
        file_name = f"words_de_basic/{sol_len}"

        if file_name not in FILE_NAMES:
            # don't test with this length
            # we don't have any words with this length
            continue

        solutions.update(
            test_word
            for test_word in get_words(file_name)
            if test_word not in ignore and distance(word, test_word) == 1
        )

    return solutions


async def get_ranked_solutions(
    word: str, before: Iterable[str] = tuple()
) -> list[tuple[int, str]]:
    """Find solutions for the word and rank them."""
    sols = await find_solutions(word)

    ranked_sols: list[tuple[int, str]] = [
        (
            len(tuple(_s for _s in await find_solutions(sol, (*before, word)))),
            sol,
        )
        for sol in sols
        if sol != word and sol not in before
    ]

    ranked_sols.sort(reverse=True)
    return ranked_sols


class WordGameHelper(HTMLRequestHandler):
    """The request handler for the word game helper page."""

    RATELIMIT_GET_LIMIT = 10

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the word game helper page."""
        if head:
            return
        word: str = str(self.get_query_argument("word", default="")).lower()

        before_str: str = str(self.get_query_argument("before", default=""))

        before = [
            _w.strip() for _w in before_str.split(",") if len(_w.strip()) > 0
        ]

        # get the new_before as set with only unique words
        new_before = (
            before if not word and word not in before else [*before, word]
        )

        await self.render(
            "pages/word_game_helper.html",
            word=word,
            words=await get_ranked_solutions(word, before),
            before=", ".join(before),
            new_before=", ".join(new_before),
        )


class WordGameHelperAPI(APIRequestHandler):
    """The request handler for the word game helper API."""

    RATELIMIT_GET_LIMIT = 10
    ALLOWED_METHODS = ("GET",)

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the word game helper API."""
        if head:
            return
        word: str = str(self.get_query_argument("word", default="")).lower()

        before_str: str = str(self.get_query_argument("before", default=""))

        before = tuple(
            _w.strip() for _w in before_str.split(",") if len(_w.strip()) > 0
        )

        return await self.finish(
            {
                "before": before,
                "word": word,
                "solutions": await get_ranked_solutions(word, before),
            }
        )
