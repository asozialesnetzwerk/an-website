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

"""Module for the word game helper."""
from __future__ import annotations

from typing import Optional

# pylint: disable=no-name-in-module
from Levenshtein import distance  # type: ignore

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo, n_from_set
from . import FILE_NAMES, get_words


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            ("/wortspiel-helfer/", WordGameHelper),
            ("/wortspiel-helfer/api/", WordGameHelperApi),
        ),
        name="Wortspiel-Helfer",
        description="Findet Worte, die nur eine Änderung "
        "von einander entfernt sind.",
        path="/wortspiel-helfer/",
        keywords=("Wortspiel", "Helfer", "Hilfe", "Worte"),
        aliases=("/word-game-helper/",),
        hidden=True,
    )


async def find_solutions(
    word: str, max_words: Optional[int] = None
) -> set[str]:
    """Find words that have only one different letter."""
    solutions: set[str] = set()

    word_len = len(word)

    if word_len == 0:
        return solutions

    for sol_len in (word_len - 1, word_len, word_len + 1):
        file_name = f"words_de/{sol_len}"

        if file_name not in FILE_NAMES:
            # don't test with this length
            # we don't have any words with this length
            continue

        solutions.update(
            test_word
            for test_word in get_words(file_name)
            if distance(word, test_word) == 1
        )

    if max_words is None:
        return solutions

    return n_from_set(solutions, max_words)


class WordGameHelper(BaseRequestHandler):
    """The request handler for the word game helper page."""

    RATELIMIT_TOKENS = 4

    async def get(self):
        """Handle get requests to the word game helper page."""
        word = self.get_query_argument("word", default="").lower()
        max_words = min(
            100, int(self.get_query_argument("max_words", default="20"))
        )
        await self.render(
            "pages/word_game_helper.html",
            word=word,
            words=await find_solutions(word, max_words),
            max_words=max_words,
        )


class WordGameHelperApi(APIRequestHandler):
    """The request handler for the word game helper api."""

    RATELIMIT_TOKENS = 3
    ALLOWED_METHODS = ("get",)

    async def get(self):
        """Handle get requests to the word game helper api."""
        word = self.get_query_argument("word", default="").lower()
        max_words = min(
            100, int(self.get_query_argument("max_words", default="20"))
        )
        await self.finish(
            {
                "word": word,
                "max_words": max_words,
                "solutions": list(await find_solutions(word, max_words)),
            }
        )
