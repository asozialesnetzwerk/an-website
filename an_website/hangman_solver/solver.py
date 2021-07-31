from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import asdict, dataclass, field

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
WORDS: dict[str, set[str]] = {}
LETTERS: dict[str, dict[str, int]] = {}
LANGUAGES: set[str] = set()

# load word lists
BASE_WORDS_DIR = f"{DIR}/words"
for folder in os.listdir(BASE_WORDS_DIR):
    if folder.startswith("words_"):
        LANGUAGES.add(folder[6:])  # without: "words_"
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
    """Create and return the ModuleInfo for this module."""
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
    words: set[str] = field(default_factory=set)
    word_count: int = 0
    letters: dict[str, int] = field(default_factory=dict)
    crossword_mode: bool = False
    max_words: int = 20
    lang: str = "de_only_a-z"


def fix_input_str(_input):
    return WILDCARDS_REGEX.sub(
        lambda m: "_" * length_of_match(m), _input.lower().strip()
    )[:100]


def fix_invalid(invalid):
    return NOT_WORD_CHAR.sub(
        "", "".join(set(invalid.lower()))
    )  # replace stuff that could be bad


async def generate_pattern_str(
    input_str: str, invalid: str, crossword_mode: bool
) -> str:
    input_str = input_str.lower()

    # in crossword_mode it doesn't matter
    # if the letters are already in input_str:
    if not crossword_mode:
        # add if not cw_mode
        invalid += input_str

    invalid_chars = fix_invalid(invalid)

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
) -> tuple[set[str], dict[str, int]]:
    input_letters: str = WILDCARDS_REGEX.sub("", input_str)
    matches_always = len(invalid) == 0 and len(input_letters) == 0

    if matches_always and not crossword_mode:
        return WORDS[file_name], LETTERS[file_name]

    pattern = await generate_pattern_str(input_str, invalid, crossword_mode)
    regex = re.compile(pattern, re.ASCII)

    current_words: set[str] = set()
    letter_list: list[str] = []

    for line in WORDS[file_name]:
        if matches_always or regex.fullmatch(line) is not None:
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
        input_chars: list[tuple[str, int]] = Counter(
            input_letters
        ).most_common(30)
        update_dict: dict[str, int] = {}
        for (_k, _v) in input_chars:
            update_dict[_k] = n_word_count * _v
        letters.update(update_dict)

    # put letters in sorted dict:
    sorted_letters: dict[str, int] = dict(letters.most_common(30))  # 26 + äöüß

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
    if language not in LANGUAGES:
        raise HTTPError(400, reason=f"'{language}' is an invalid language")

    input_str = fix_input_str(input_str)
    invalid = fix_invalid(invalid)

    input_len = len(input_str)

    # to be short (is only the key of the words dict in __init__.py)
    file_name = (  # pylint: disable=redefined-outer-name
        f"words_{language}/{input_len}"
    )

    if file_name not in WORDS:
        # no words with the length
        return Hangman(
            input=input_str,
            invalid=invalid,
            crossword_mode=crossword_mode,
            max_words=max_words,
            lang=language,
        )

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
        language,
    )


async def handle_request(request_handler: RequestHandler) -> Hangman:
    max_words = max(
        0,
        min(
            100,
            int(
                str(
                    request_handler.get_query_argument(
                        "max_words", default="20"
                    )
                )
            ),
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
    RATELIMIT_TOKENS = 3

    async def get(self, *args):  # pylint: disable=unused-argument
        hangman = await handle_request(self)
        await self.render("pages/hangman_solver.html", **asdict(hangman))


class HangmanSolverAPI(APIRequestHandler):
    RATELIMIT_TOKENS = 3

    async def get(self, *args):  # pylint: disable=unused-argument
        hangman = await handle_request(self)
        hangman_dict = asdict(hangman)
        hangman_dict["words"] = list(hangman_dict["words"])
        self.write(hangman_dict)
