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
from tornado.web import HTTPError

from an_website.hangman_solver import hangman_solver as solver


def test_solving_hangman() -> None:
    """Test solving hangman puzzles."""
    # pylint: disable=protected-access
    hangman: solver.Hangman = solver._solve_hangman(
        input_str="te_t",
        invalid="x",
        language="de",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert hangman.letters["s"] == 1

    hangman = solver._solve_hangman(
        input_str="_est",
        invalid="n",
        language="de",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = solver._solve_hangman(
        input_str="_est",
        invalid="x",
        language="de",
        max_words=10,
        crossword_mode=False,
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = solver._solve_hangman(
        input_str="_est",
        invalid="x",
        language="de",
        max_words=10,
        crossword_mode=True,
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert hangman.letters["t"] == 1

    hangman = solver._solve_hangman(
        input_str="______",
        invalid="e",
        language="de",
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
        language="de_umlauts",
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
    test_solving_hangman()
