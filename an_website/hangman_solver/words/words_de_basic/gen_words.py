#!/usr/bin/env python3

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

from __future__ import annotations

import json  # pylint: disable=preferred-module

FILE = "full_wordlist.txt"

if __name__ == "__main__":
    with open(FILE, encoding="utf-8") as file:
        text = file.read().lower()
    words = text.splitlines()
    words_sorted = sorted(set(words))  # sort words unique

    letters: dict[str, dict[str, int]] = {}
    for word in words_sorted:
        length = str(len(word))
        with open(length + ".txt", "a", encoding="utf-8") as file:
            file.write(word)
            file.write("\n")
        print(word)
        m = letters.get(length, {})
        for index, letter in enumerate(word):
            if word.index(letter) is index:
                m[letter] = m.get(letter, 0) + 1
        letters[length] = m

    print("Generating letters:")

    for key, value in letters.items():
        letters_items: list[tuple[str, int]] = list(value.items())
        sorted_letters: list[tuple[str, int]] = sorted(
            letters_items, key=lambda item: item[1], reverse=True
        )
        sorted_letters_json = json.dumps(dict(sorted_letters))
        print(key, sorted_letters_json)

        with open(key + ".json", "w", encoding="utf-8") as file:
            file.write(sorted_letters_json)
