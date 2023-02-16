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

"""Nobody inspects the spammish repetition."""

from __future__ import annotations

import json  # pylint: disable=preferred-module
from collections import Counter
from pathlib import Path

DIR = Path(__file__).parent
FILE = DIR / "full_wordlist.txt"


if __name__ == "__main__":
    with open(FILE, encoding="UTF-8") as file:
        text = file.read().lower()
    words = text.splitlines()
    words_sorted = sorted(set(words))  # sort words unique

    letters: dict[int, Counter[str]] = {}
    for word in words_sorted:
        length = len(word)
        with open(DIR / f"{length}.txt", "ab") as file:
            file.write(word.encode("CP1252"))
            file.write(b"\n")
        counter = letters.setdefault(length, Counter())
        counter.update(set(word))

    print("Generating letters")

    for key, value in letters.items():
        sorted_letters: list[tuple[str, int]] = sorted(
            value.items(), key=lambda item: item[1], reverse=True
        )
        sorted_letters_json = json.dumps(dict(sorted_letters))

        with open(DIR / f"{key}.json", "w", encoding="UTF-8") as file:
            file.write(sorted_letters_json)
