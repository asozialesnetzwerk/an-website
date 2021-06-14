from __future__ import annotations
from typing import Dict, Tuple, List
from distutils.util import strtobool
from dataclasses import dataclass, field, asdict
import os
import re

from tornado.web import RequestHandler, HTTPError

from ..utils.utils import RequestHandlerCustomError, RequestHandlerJsonAPI, length_of_match

WILDCARDS_REGEX = re.compile(r"[_?-]+")
NOT_WORD_CHAR = re.compile(r"[^a-zA-ZäöüßÄÖÜẞ]+")


@dataclass()
class Hangman:
    input: str = ""
    invalid: str = ""
    words: list[str] = field(default_factory=list[str])
    word_count: int = 0
    letters: dict[str, int] = field(default_factory=dict[str, int])
    crossword_mode: bool = False
    max_words: int = 100
    lang: str = "de_only_a-z"


async def generate_pattern_str(input_str: str, invalid: str, crossword_mode: bool) -> str:
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

    return WILDCARDS_REGEX.sub(lambda m: (wild_card_replacement + "{" + str(length_of_match(m)) + "}"), input_str)


async def get_words_and_letters(file_name: str, input_str: str, invalid: str, crossword_mode: bool) \
        -> tuple[list[str], dict[str, int]]:
    pattern = await generate_pattern_str(input_str, invalid, crossword_mode)
    regex = re.compile(pattern, re.ASCII)

    input_set = set(input_str.lower())

    words = []
    letters: dict[str, int] = {}
    with open(file_name) as file:
        for line in file:
            stripped_line = line.strip()
            if regex.fullmatch(stripped_line) is not None:
                words.append(stripped_line)

                # do letter stuff:
                for letter in set(stripped_line):
                    if letter not in input_set:
                        letters[letter] = letters.setdefault(letter, 0) + 1

    # sort letters:
    letters_items: List[Tuple[str, int]] = [(k, v) for k, v in letters.items()]
    sorted_letters: List[Tuple[str, int]] = sorted(letters_items, key=lambda item: item[1], reverse=True)

    return words, dict(sorted_letters)


async def solve_hangman(request_handler: RequestHandler) -> Hangman:
    max_words = int(str(request_handler.get_query_argument("max_words", default="100")))
    crossword_mode_str = str(request_handler.get_query_argument("crossword_mode", default="False"))
    crossword_mode = bool(strtobool(crossword_mode_str))  # if crossword mode

    language = str(request_handler.get_query_argument("lang", default="de"))

    folder = f"hangman_solver/words/words_{language}"

    if not os.path.isdir(folder):
        raise HTTPError(400, f"'{language}' is an invalid language")

    input_str = str(request_handler.get_query_argument("input", default=""))
    input_len = len(input_str)
    if input_len == 0:  # input is empty:
        return Hangman(crossword_mode=crossword_mode, max_words=max_words, lang=language)

    invalid = str(request_handler.get_query_argument("invalid", default=""))

    file_name = f"{folder}/{input_len}.txt"

    words_and_letters = await get_words_and_letters(file_name, input_str, invalid, crossword_mode)
    words = words_and_letters[0]
    letters = words_and_letters[1]

    return Hangman(input_str, invalid, words, len(words), letters, crossword_mode, max_words)


class HangmanSolver(RequestHandlerCustomError):
    async def get(self, *args):
        hangman = await solve_hangman(self)
        await self.render("pages/hangman_solver.html", **asdict(hangman))


class HangmanSolverAPI(RequestHandlerJsonAPI):
    async def get(self, *args):
        hangman = await solve_hangman(self)
        self.write(asdict(hangman))
