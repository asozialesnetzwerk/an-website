from __future__ import annotations, barry_as_FLUFL

import os
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Set, Tuple

import orjson
from tornado.web import HTTPError, RequestHandler

from ..utils.utils import (
    APIRequestHandler,
    BaseRequestHandler,
    ModuleInfo,
    length_of_match,
    n_from_set,
    strtobool,
)
from . import DIR

WILDCARDS_REGEX = re.compile(r"[_?-]+")
NOT_WORD_CHAR = re.compile(r"[^a-zA-ZäöüßÄÖÜẞ]+")

# example: {"words_en/3": ["you", "she", ...]}
WORDS: Dict[str, Set[str]] = {}
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
                    WORDS[key] = set(file.read().splitlines())
            if file_name.endswith(".json"):
                with open(f"{words_dir}/{file_name}") as file:
                    LETTERS[key] = orjson.loads(file.read())

del (  # pylint: disable=undefined-loop-variable
    folder,
    words_dir,
    file_name,
    file,
    key,
)


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (r"/hangman-l(ö|oe|%C3%B6)ser/?", HangmanSolver),
            (r"/hangman-l(ö|oe|%C3%B6)ser/api/?", HangmanSolverAPI),
        ),
        name="Hangman-Löser",
        description="Ein Website, die Lösungen für Galgenmännchen findet",
        path="/hangman-loeser",
    )


@dataclass()
class Hangman:  # pylint: disable=too-many-instance-attributes
    input: str = ""
    invalid: str = ""
    words: Set[str] = field(default_factory=set)
    word_count: int = 0
    letters: Dict[str, int] = field(default_factory=dict)
    crossword_mode: bool = False
    max_words: int = 20
    lang: str = "de_only_a-z"


async def generate_pattern_str(
    input_str: str, invalid: str, crossword_mode: bool
) -> str:
    input_str = input_str.lower()
    invalid = invalid.lower()

    # in crossword_mode it doesn't matter
    # if the letters are already in input_str:
    if not crossword_mode:
        # add if not cw_mode
        invalid += input_str

    invalid_chars = NOT_WORD_CHAR.sub(
        "", invalid
    )  # replace stuff that could be bad

    if len(invalid_chars) == 0:
        # there are no invalid chars,
        # so the wildcard can be replaced with just "."
        return WILDCARDS_REGEX.sub(
            lambda m: "." * length_of_match(m), input_str
        )

    wild_card_replacement = "[^" + invalid_chars + "]"

    return WILDCARDS_REGEX.sub(
        lambda m: (
            wild_card_replacement + "{" + str(length_of_match(m)) + "}"
        ),
        input_str,
    )


async def get_words_and_letters(  # pylint: disable=too-many-locals
    file_name: str,  # pylint: disable=redefined-outer-name
    input_str: str,
    invalid: str,
    crossword_mode: bool,
) -> Tuple[Set[str], Dict[str, int]]:
    input_letters: str = WILDCARDS_REGEX.sub("", input_str)
    matches_always = len(invalid) == 0 and len(input_letters) == 0

    if matches_always:
        return WORDS[file_name], LETTERS[file_name]

    pattern = await generate_pattern_str(input_str, invalid, crossword_mode)
    regex = re.compile(pattern, re.ASCII)

    current_words: Set[str] = set()
    letter_list: List[str] = []

    for line in WORDS[file_name]:
        if regex.fullmatch(line) is not None:
            current_words.add(line)

            # add letters to list
            if crossword_mode:
                letter_list.extend(line)
            else:
                # add every letter only once
                letter_list.extend(set(line))

    # count letters:
    letters = Counter(letter_list)

    if crossword_mode:
        n_word_count = -1 * len(current_words)
        input_chars: List[Tuple[str, int]] = Counter(
            input_letters
        ).most_common(30)
        update_dict: Dict[str, int] = {}
        for (_k, _v) in input_chars:
            update_dict[_k] = n_word_count * _v
        letters.update(update_dict)

    # put letters in sorted dict:
    sorted_letters: Dict[str, int] = dict(letters.most_common(30))  # 26 + äöüß

    if not crossword_mode:
        # remove letters that are already in input
        for letter in set(input_letters.lower()):
            if letter in sorted_letters:
                del sorted_letters[letter]

    return current_words, sorted_letters


async def solve_hangman(
    input_str: str,
    invalid: str,
    language: str,
    max_words: int,
    crossword_mode: bool,
) -> Hangman:
    input_len = len(input_str)

    if input_len == 0:  # input is empty:
        return Hangman(
            crossword_mode=crossword_mode, max_words=max_words, lang=language
        )

    # to be short (is only the key of the words dict in __init__.py)
    file_name = (  # pylint: disable=redefined-outer-name
        f"words_{language}/{input_len}"
    )

    if file_name not in WORDS:
        raise HTTPError(400, reason=f"'{language}' is an invalid language")

    # do the solving:
    matched_words, letters = await get_words_and_letters(
        file_name, input_str, invalid, crossword_mode
    )

    return Hangman(
        input_str,
        invalid,
        n_from_set(matched_words, max_words),
        len(matched_words),
        letters,
        crossword_mode,
        max_words,
    )


async def handle_request(request_handler: RequestHandler) -> Hangman:
    max_words = min(
        100,
        int(
            str(request_handler.get_query_argument("max_words", default="20"))
        ),
    )

    crossword_mode_str = str(
        request_handler.get_query_argument("crossword_mode", default="False")
    )
    crossword_mode = strtobool(crossword_mode_str)  # if crossword mode

    language = str(
        request_handler.get_query_argument("lang", default="de_only_a-z")
    )

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
        hangman_dict = asdict(hangman)
        hangman_dict["words"] = list(hangman_dict["words"])
        self.write(hangman_dict)
