#!/usr/bin/env python3
# pylint: disable=invalid-name

file = "full_wordlist.txt"

text = open(file).read().lower()\
    .replace("ä", "ae")\
    .replace("ö", "oe")\
    .replace("ü", "ue")\
    .replace("ß", "ss")

with open(file, "w") as file:
    file.write(text)
