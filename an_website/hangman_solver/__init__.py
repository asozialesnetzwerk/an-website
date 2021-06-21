from __future__ import annotations, barry_as_FLUFL

import os
import time
from typing import Dict, List

DIR = os.path.dirname(__file__)

# example: {"words_en/3.txt": ["you", "she", ...]}
words: Dict[str, List[str]] = {}

t = time.time()
# fill words, with all word lists:
base_words_dir = f"{DIR}/words"
for folder in os.listdir(base_words_dir):
    if folder.startswith("words_"):
        words_dir = f"{base_words_dir}/{folder}"
        for file_name in os.listdir(words_dir):
            if file_name.endswith(".txt"):
                with open(f"{words_dir}/{file_name}") as file:
                    words[f"{folder}/{file_name}"] = file.read().splitlines()
