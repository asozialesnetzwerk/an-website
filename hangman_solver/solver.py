import os
import re
from distutils.util import strtobool

from tornado.web import RequestHandler

from utils.utils import get_url, RequestHandlerCustomError, RequestHandlerJsonApi

WILDCARDS_REGEX = re.compile(r"[_?-]+")
NOT_WORD_CHAR = re.compile(r"[^a-zA-ZäöüßÄÖÜẞ]+")


def get_word_dict(input_str: str = "", invalid: str = "", words: list = None, allow_umlauts: bool = False,
                  crossword_mode: bool = False, max_words: int = 100) -> dict:
    if words is None:
        words = []
    return {"input": input_str,
            "invalid": invalid,
            "words": words[:max_words],
            "word_count": len(words),
            "letters": get_letters(words, input_str),
            "allow_umlauts": allow_umlauts,
            "crossword_mode": crossword_mode,
            "max_words": max_words
            }


def length_of_match(m: re.Match) -> int:
    span = m.span()
    return span[1] - span[0]


def generate_pattern_str(input_str: str, invalid: str, crossword_mode: bool) -> str:
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


def search_words(file_name: str, pattern: str) -> list:
    regex = re.compile(pattern, re.ASCII)
    words = []
    with open(file_name) as file:
        for line in file:
            if regex.fullmatch(line.strip()) is not None:
                words.append(line)

    return words


def get_letters(words: list, input_str: str) -> dict:
    input_set = set(input_str.lower())

    letters = {}
    for word in words:
        for letter in set(word):
            if letter not in input_set:
                letters[letter] = letters.get(letter, default=0) + 1

    return dict(sorted(letters.items(), key=lambda item: item[1], reverse=True))


def find_words(request_handler: RequestHandler) -> dict:
    max_words = int(request_handler.get_query_argument("max_words", default="100"))
    allow_umlauts_str = request_handler.get_query_argument("allow_umlauts", default="False")
    crossword_mode_str = request_handler.get_query_argument("crossword_mode", default="False")
    allow_umlauts = bool(strtobool(allow_umlauts_str))  # if the words can contain ä,ö,ü
    crossword_mode = bool(strtobool(crossword_mode_str))  # if crossword mode

    input_str = request_handler.get_query_argument("input", default="")
    input_len = len(input_str)
    if input_len == 0:  # input is empty:
        return get_word_dict(allow_umlauts=allow_umlauts, crossword_mode=crossword_mode, max_words=max_words)

    invalid = request_handler.get_query_argument("invalid", default="")
    language = request_handler.get_query_argument("lang", default="de")

    folder = f"hangman_solver/words/words_{language}"
    if language == "de" and not allow_umlauts:
        folder += "_only_a-z"

    if not os.path.isdir(folder):
        return {"error": "Invalid language."}

    file_name = f"{folder}/{input_len}.txt"

    pattern = generate_pattern_str(input_str, invalid, crossword_mode)

    words = search_words(file_name, pattern)

    return get_word_dict(input_str, invalid, words, allow_umlauts, crossword_mode, max_words)


class HangmanSolver(RequestHandlerCustomError):
    def get(self, *args):
        words_dict = find_words(self)

        if words_dict.get("error"):
            self.write_error(400, exc_info=words_dict.get("error"))
            return

        self.render("pages/hangman_solver.html", **words_dict)


class HangmanSolverApi(RequestHandlerJsonApi):
    def get(self, *args):
        words_dict = find_words(self)

        self.write_json(words_dict)
