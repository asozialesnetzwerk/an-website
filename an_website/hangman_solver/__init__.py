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

"""The pages that helps solving hangman puzzles."""
from __future__ import annotations

import os

DIR = os.path.dirname(__file__)


LANGUAGES: set[str] = set()

BASE_WORD_DIR = f"{DIR}/words"


def get_file_names_words_and_letters() -> tuple[str, ...]:
    """
    Find all the words and return a tuple of their file_names.

    Additionally add all the languages to LANGUAGES.
    """
    file_names: set[str] = set()
    # iterate over the folders in the words dir
    for folder in os.listdir(BASE_WORD_DIR):
        # check if the folder is a words folder
        if folder.startswith("words_"):
            # add the language found in the word dir to LANGUAGES
            LANGUAGES.add(folder[6:])  # without: "words_"
            # the dir with the words in the current lang
            words_dir = f"{BASE_WORD_DIR}/{folder}"
            for file_name in os.listdir(words_dir):
                # ignore python files
                if not file_name.endswith(".py"):
                    # the relativ file name
                    rel_file_name = f"{folder}/{file_name}"

                    # add the file name without the extension to file_names
                    file_names.add(rel_file_name.split(".", 1)[0])

    return tuple(file_names)


FILE_NAMES: tuple[str, ...] = get_file_names_words_and_letters()