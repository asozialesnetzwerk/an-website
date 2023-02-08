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

import os
from functools import lru_cache
from pathlib import Path
from typing import Final, cast

import orjson as json
from typed_stream import FileStream, Stream

DIR: Final = os.path.dirname(__file__)


BASE_WORD_DIR: Final = Path(DIR) / "words"


def get_filenames_and_languages() -> tuple[frozenset[str], frozenset[str]]:
    """
    Find all the words and return a tuple of their file names and languages.

    The file names are each in a frozenset to guarantee immutability.
    """
    languages: set[str] = set()
    return frozenset(
        Stream(BASE_WORD_DIR.iterdir())
        .filter(Path.is_dir)
        .filter(lambda folder: folder.name != "__pycache__")
        .peek(lambda folder: languages.add(folder.name))
        .flat_map(lambda folder: folder.glob("[0123456789]*.json"))
        .map(lambda file: file.relative_to(BASE_WORD_DIR).with_suffix(""))
        .map(str)
    ), frozenset(languages)


FILE_NAMES, LANGUAGES = get_filenames_and_languages()


@lru_cache(10)
def get_words(filename: str) -> frozenset[str]:
    """Get the words with the filename and return them."""
    return frozenset(
        FileStream(BASE_WORD_DIR / f"{filename}.txt").map(str.rstrip)
    )


@lru_cache(10)
def get_letters(filename: str) -> dict[str, int]:
    """Get the letters dict with the filename and return it."""
    file = BASE_WORD_DIR / f"{filename}.json"
    return cast(dict[str, int], json.loads(file.read_text(encoding="UTF-8")))
