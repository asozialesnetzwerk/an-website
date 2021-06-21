#!/usr/bin/env python3
# pylint: disable=invalid-name

from __future__ import annotations, barry_as_FLUFL

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
    print("length: " + key)
    print_val = []
    for k2, v2 in sorted(value.items(), key=lambda x: x[1], reverse=True):
        print_val.append(k2)
        print_val.append(": ")
        print_val.append(str(v2))
        print_val.append(", ")
    del print_val[-1]  # delete last item
    with open(key + "_letters.txt", "w") as file:
        file.write("".join(print_val))
