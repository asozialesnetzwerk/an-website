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
from typing import Final, cast

import orjson as json

DIR: Final = os.path.dirname(__file__)


BASE_WORD_DIR: Final = os.path.join(DIR, "words")


def get_filenames_and_languages() -> tuple[frozenset[str], frozenset[str]]:
    """
    Find all the words and return a tuple of their file names and languages.

    The file names are each in a frozenset to guarantee immutability.
    """
    languages: set[str] = set()
    filenames: set[str] = set()
    # iterate over the folders in the words dir
    for folder in os.listdir(BASE_WORD_DIR):
        # check if the folder is a words folder
        if folder.startswith("words_"):
            # add the language found in the word dir to LANGUAGES
            languages.add(folder[6:])  # without: "words_"
            # the dir with the words in the current lang
            words_dir = os.path.join(BASE_WORD_DIR, folder)
            for filename in os.listdir(words_dir):
                # ignore python files
                if not filename.endswith(".py"):
                    # the relativ file name
                    rel_filename = f"{folder}/{filename}"

                    # add the file name without the extension to filenames
                    filenames.add(rel_filename.split(".", 1)[0])

    return frozenset(filenames), frozenset(languages)


FILE_NAMES, LANGUAGES = get_filenames_and_languages()


@lru_cache(10)
def get_words(filename: str) -> frozenset[str]:
    """Get the words with the filename and return them."""
    with open(
        os.path.join(BASE_WORD_DIR, f"{filename}.txt"), encoding="UTF-8"
    ) as file:
        return frozenset(file.read().splitlines())


@lru_cache(10)
def get_letters(filename: str) -> dict[str, int]:
    """Get the letters dict with the filename and return it."""
    with open(
        os.path.join(BASE_WORD_DIR, f"{filename}.json"), encoding="UTF-8"
    ) as file:
        # we know the files, so we know the type
        return cast(dict[str, int], json.loads(file.read()))
