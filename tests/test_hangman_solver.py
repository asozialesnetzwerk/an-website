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
from hangman_solver import HangmanResult
from tornado.web import HTTPError

from an_website.hangman_solver import hangman_solver as solver


def test_solving_hangman() -> None:
    """Test solving hangman puzzles."""
    hangman: HangmanResult = solver.solve_hangman(
        solver.HangmanArguments(
            input="te_t",
            invalid="x",
            lang="de",
            max_words=10,
            crossword_mode=False,
        ),
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert dict(hangman.letter_frequency)["s"] == 1

    hangman = solver.solve_hangman(
        solver.HangmanArguments(
            input="_est",
            invalid="n",
            lang="de",
            max_words=10,
            crossword_mode=False,
        ),
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = solver.solve_hangman(
        solver.HangmanArguments(
            input="_est",
            invalid="x",
            lang="de",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert "test" not in hangman.words

    hangman = solver.solve_hangman(
        solver.HangmanArguments(
            input="_est",
            invalid="x",
            lang="de",
            max_words=10,
            crossword_mode=True,
        )
    )

    assert len(hangman.words) <= 10
    assert "test" in hangman.words
    assert dict(hangman.letter_frequency)["t"] == 1

    hangman = solver.solve_hangman(
        solver.HangmanArguments(
            input="______",
            invalid="e",
            lang="de",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert hangman.matching_words_count > 10
    assert "e" not in dict(hangman.letter_frequency)
    assert "ä" not in dict(hangman.letter_frequency)
    assert "ö" not in dict(hangman.letter_frequency)
    assert "ü" not in dict(hangman.letter_frequency)

    hangman = solver.solve_hangman(
        solver.HangmanArguments(
            input="______",
            invalid="",
            lang="de_umlauts",
            max_words=10,
            crossword_mode=False,
        )
    )

    assert len(hangman.words) <= 10
    assert hangman.matching_words_count > 10
    assert "ä" in dict(hangman.letter_frequency)

    with pytest.raises(HTTPError):
        solver.solve_hangman(
            solver.HangmanArguments(
                input="",
                invalid="",
                lang="invalid",
                max_words=0,
                crossword_mode=False,
            )
        )


if __name__ == "__main__":
    test_solving_hangman()
