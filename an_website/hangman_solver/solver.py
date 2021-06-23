from __future__ import annotations, barry_as_FLUFL

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from distutils.util import strtobool
from typing import Dict, List, Tuple

from tornado.web import HTTPError, RequestHandler

from ..utils.utils import APIRequestHandler, BaseRequestHandler, length_of_match
from . import DIR

WILDCARDS_REGEX = re.compile(r"[_?-]+")
NOT_WORD_CHAR = re.compile(r"[^a-zA-ZäöüßÄÖÜẞ]+")

# example: {"words_en/3.txt": ["you", "she", ...]}
WORDS: Dict[str, List[str]] = {}
LETTERS: Dict[str, Dict[str, int]] = {}
# load word lists
BASE_WORDS_DIR = f"{DIR}/words"
for folder in os.listdir(BASE_WORDS_DIR):
    if folder.startswith("words_"):
        words_dir = f"{BASE_WORDS_DIR}/{folder}"
        for file_name in os.listdir(words_dir):
            key = f"{folder}/{file_name}".split(".")[0]
            if file_name.endswith(".txt"):
                with open(f"{words_dir}/{file_name}") as file:
                    WORDS[key] = file.read().splitlines()
            if file_name.endswith(".json"):
                with open(f"{words_dir}/{file_name}") as file:
                    LETTERS[key] = json.loads(file.read())

del folder, words_dir, file_name, file, key  # pylint: disable=undefined-loop-variable


def get_handlers():
    return (
        (r"/hangman-l(ö|oe|%C3%B6)ser/?", HangmanSolver),
        (r"/hangman-l(ö|oe|%C3%B6)ser/api/?", HangmanSolverAPI),
    )


@dataclass()
class Hangman:  # pylint: disable=too-many-instance-attributes
    input: str = ""
    invalid: str = ""
    words: List[str] = field(default_factory=list)
    word_count: int = 0
    letters: Dict[str, int] = field(default_factory=dict)
    crossword_mode: bool = False
    max_words: int = 100
    lang: str = "de_only_a-z"


async def generate_pattern_str(
    input_str: str, invalid: str, crossword_mode: bool
) -> str:
    input_str = input_str.lower()
    invalid = invalid.lower()

    # in crossword_mode it doesn't matter if the letters are already in input_str:
    if not crossword_mode:
        # add if not cw_mode
        invalid += input_str

    invalid_chars = NOT_WORD_CHAR.sub("", invalid)  # replace stuff that could be bad

    if len(invalid_chars) == 0:
        # there are no invalid chars, so the wildcard can be replaced with just "."
        return WILDCARDS_REGEX.sub(lambda m: "." * length_of_match(m), input_str)

    wild_card_replacement = "[^" + invalid_chars + "]"

    return WILDCARDS_REGEX.sub(
        lambda m: (wild_card_replacement + "{" + str(length_of_match(m)) + "}"),
        input_str,
    )


def sort_letters(letters: Dict[str, int]) -> Dict[str, int]:
    letters_items: List[Tuple[str, int]] = list(letters.items())
    sorted_letters: List[Tuple[str, int]] = sorted(
        letters_items, key=lambda item: item[1], reverse=True
    )
    return dict(sorted_letters)


async def get_words_and_letters(
    file_name: str,  # pylint: disable=redefined-outer-name
    input_str: str,
    invalid: str,
    crossword_mode: bool,
) -> Tuple[List[str], Dict[str, int]]:
    matches_always = len(invalid) == 0 and len(WILDCARDS_REGEX.sub("", input_str)) == 0

    if matches_always:
        return WORDS[file_name], LETTERS[file_name]

    pattern = await generate_pattern_str(input_str, invalid, crossword_mode)
    regex = re.compile(pattern, re.ASCII)

    input_set = set(input_str.lower())

    current_words = []
    letters: dict[str, int] = {}

    for line in WORDS[file_name]:
        if regex.fullmatch(line) is not None:
            current_words.append(line)

            # do letter stuff:
            for letter in set(line):
                if letter not in input_set:
                    letters[letter] = letters.setdefault(letter, 0) + 1

    return current_words, sort_letters(letters)


async def solve_hangman(
    input_str: str, invalid: str, language: str, max_words: int, crossword_mode: bool
) -> Hangman:
    input_len = len(input_str)

    if input_len == 0:  # input is empty:
        return Hangman(
            crossword_mode=crossword_mode, max_words=max_words, lang=language
        )

    # to be short (is only the key of the words dict in __init__.py)
    file_name = f"words_{language}/{input_len}"  # pylint: disable=redefined-outer-name

    if file_name not in WORDS:
        raise HTTPError(400, reason=f"'{language}' is an invalid language")

    # do the solving:
    matched_words, letters = await get_words_and_letters(
        file_name, input_str, invalid, crossword_mode
    )

    return Hangman(
        input_str,
        invalid,
        matched_words,
        len(matched_words),
        letters,
        crossword_mode,
        max_words,
    )


async def handle_request(request_handler: RequestHandler) -> Hangman:
    max_words = int(str(request_handler.get_query_argument("max_words", default="20")))

    crossword_mode_str = str(
        request_handler.get_query_argument("crossword_mode", default="False")
    )
    crossword_mode = bool(strtobool(crossword_mode_str))  # if crossword mode

    language = str(request_handler.get_query_argument("lang", default="de_only_a-z"))

    input_str = str(request_handler.get_query_argument("input", default=""))

    invalid = str(request_handler.get_query_argument("invalid", default=""))

    return await solve_hangman(
        max_words=max_words,
        crossword_mode=crossword_mode,
        language=language,
        input_str=input_str,
        invalid=invalid,
    )


class HangmanSolver(BaseRequestHandler):
    async def get(self, *args):  # pylint: disable=unused-argument
        hangman = await handle_request(self)
        await self.render("pages/hangman_solver.html", **asdict(hangman))


class HangmanSolverAPI(APIRequestHandler):
    async def get(self, *args):  # pylint: disable=unused-argument
        hangman = await handle_request(self)
        self.write(asdict(hangman))
