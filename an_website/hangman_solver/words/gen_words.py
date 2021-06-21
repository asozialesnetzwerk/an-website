#!/usr/bin/env python3
# pylint: disable=invalid-name

from __future__ import annotations, barry_as_FLUFL

file = "full_wordlist.txt"

text = open(file).read().lower()
words = text.splitlines()
words_sorted = sorted(set(words))  # sort words unique

for word in words_sorted:
    length = str(len(word))
    with open(length + ".txt", "a") as file:
        file.write(word)
        file.write("\n")
    print(word)
