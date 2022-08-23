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

"""The tests for the hangman solver."""

from __future__ import annotations

import pytest
import regex
from tornado.web import HTTPError

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

    for pattern in (r"[01]", r"[01]{2}", r"[ab]", r"[ab]{2}"):
        matched_words, sorted_letters = solver.filter_words(
            words,
            regex.compile(pattern),
            "0b",
            False,
            False,
        )
        assert len(matched_words) == 2
        assert "0" not in sorted_letters
        assert "b" not in sorted_letters
        assert len(sorted_letters) == 1


def test_generate_pattern_str() -> None:
    """Test generating the pattern string."""
    pattern_str = solver.generate_pattern_str(
        input_str="_", invalid="", crossword_mode=False
    )
    assert pattern_str == "."

    pattern_str = solver.generate_pattern_str(
        input_str="___", invalid="", crossword_mode=False
    )
    assert pattern_str == "..."

    pattern_str = solver.generate_pattern_str(
        input_str="_",
        invalid="ABCcccccccccccccccccccccc",
        crossword_mode=False,
    )
    assert regex.fullmatch(r"^\[\^[abc]{3}]\{1}$", pattern_str)

    pattern_str = solver.generate_pattern_str(
        input_str="___", invalid="abc", crossword_mode=False
    )
    assert regex.fullmatch(r"^\[\^[abc]{3}]\{3}$", pattern_str)


def test_solving_hangman() -> None:
    """Test solving hangman puzzles."""
    # pylint: disable=protected-access
    hangman: solver.Hangman = solver._solve_hangman(
        input_str="te_t",
        invalid="x",
        language="de_only_a-z",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert hangman.letters["s"] == 1

    hangman = solver._solve_hangman(
        input_str="_est",
        invalid="n",
        language="de_only_a-z",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = solver._solve_hangman(
        input_str="_est",
        invalid="x",
        language="de_only_a-z",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = solver._solve_hangman(
        input_str="_est",
        invalid="x",
        language="de_only_a-z",
        max_words=10,
        crossword_mode=True,
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert hangman.letters["t"] == 1

    hangman = solver._solve_hangman(
        input_str="______",
        invalid="e",
        language="de_only_a-z",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert hangman.word_count > 10
    assert "e" not in hangman.letters
    assert "ä" not in hangman.letters
    assert "ö" not in hangman.letters
    assert "ü" not in hangman.letters

    hangman = solver._solve_hangman(
        input_str="______",
        invalid="",
        language="de",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert hangman.word_count > 10
    assert "ä" in hangman.letters

    with pytest.raises(HTTPError):
        solver._solve_hangman(
            input_str="",
            invalid="",
            language="invalid",
            max_words=0,
            crossword_mode=False,
        )


if __name__ == "__main__":
    test_filter_words()
    test_solving_hangman()
