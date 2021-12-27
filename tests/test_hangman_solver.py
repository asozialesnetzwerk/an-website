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

"""Tests for the hangman solver module."""
from __future__ import annotations

import asyncio
import re

from an_website.hangman_solver import hangman_solver as solver


def test_filter_words() -> None:
    """Test filtering words."""
    words = frozenset(
        {
            # r"[01]"
            "0",
            "1",
            # r"[01]{2}"
            "01",
            "10",
            # r"[ab]"
            "a",
            "b",
            # r"[ab]{2}"
            "ab",
            "ba",
            # match none
            "a0",
            "b1",
        }
    )

    for regex in (r"[01]", r"[01]{2}", r"[ab]", r"[ab]{2}"):
        matched_words, sorted_letters = solver.filter_words(
            words,
            re.compile(regex),
            "0b",
            False,
            False,
        )
        assert len(matched_words) == 2
        assert "0" not in sorted_letters
        assert "b" not in sorted_letters
        assert len(sorted_letters) == 1


def test_solving_hangman() -> None:
    """Test solving hangman puzzles."""
    hangman: solver.Hangman = asyncio.run(
        solver.solve_hangman(
            input_str="te_t",
            invalid="x",
            language="de_only_a-z",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert hangman.letters["s"] == 1

    hangman = asyncio.run(
        solver.solve_hangman(
            input_str="_est",
            invalid="n",
            language="de_only_a-z",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = asyncio.run(
        solver.solve_hangman(
            input_str="_est",
            invalid="x",
            language="de_only_a-z",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = asyncio.run(
        solver.solve_hangman(
            input_str="_est",
            invalid="x",
            language="de_only_a-z",
            max_words=10,
            crossword_mode=True,
        )
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert hangman.letters["t"] == 1

    hangman = asyncio.run(
        solver.solve_hangman(
            input_str="______",
            invalid="e",
            language="de_only_a-z",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert hangman.word_count > 10
    assert "e" not in hangman.letters
    assert "ä" not in hangman.letters
    assert "ö" not in hangman.letters
    assert "ü" not in hangman.letters

    hangman = asyncio.run(
        solver.solve_hangman(
            input_str="______",
            invalid=str(),
            language="de",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert hangman.word_count > 10
    assert "ä" in hangman.letters


if __name__ == "__main__":
    test_filter_words()
