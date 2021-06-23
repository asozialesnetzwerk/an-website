#!/usr/bin/env python3
# pylint: disable=invalid-name

from __future__ import annotations, barry_as_FLUFL

import json
from typing import List, Tuple

file = "full_wordlist.txt"

text = open(file).read().lower()
words = text.splitlines()
words_sorted = sorted(set(words))  # sort words unique

letters = {}
for word in words_sorted:
    length = str(len(word))
    with open(length + ".txt", "a") as file:
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
    letters_items: List[Tuple[str, int]] = list(value.items())
    sorted_letters: List[Tuple[str, int]] = sorted(
        letters_items, key=lambda item: item[1], reverse=True
    )
    sorted_letters_json = json.dumps(dict(sorted_letters))
    print(key, sorted_letters_json)

    with open(key + ".json", "w") as file:
        file.write(sorted_letters_json)
