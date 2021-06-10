import os
from distutils.util import strtobool
import json

from utils.utils import get_url, RequestHandlerCustomError


def get_word_dict(input_str="", words=None, letters=None, allow_umlauts=False, crossword_mode=False):
    if letters is None:
        letters = {}
    if words is None:
        words = []
    return {"input": input_str,
            "words": words,
            "letters": letters,
            "allow_umlauts": allow_umlauts,
            "crossword_mode": crossword_mode
            }


def

def find_words(request_handler):
    allow_umlauts_str = request_handler.get_query_argument("allow-umlauts", default="False")
    crossword_mode_str = request_handler.get_query_argument("crossword-mode", default="False")
    allow_umlauts = bool(strtobool(allow_umlauts_str))  # if the words can contain ä,ö,ü
    crossword_mode = bool(strtobool(crossword_mode_str))  # if crossword mode

    input_str = request_handler.get_query_argument("input", default="")
    input_len = len(input_str)
    if input_len == 0:  # input is empty:
        return get_word_dict(allow_umlauts=allow_umlauts, crossword_mode=crossword_mode)

    invalid = request_handler.get_query_argument("invalid", default="")
    language = request_handler.get_query_argument("lang", default="de")

    # in crossword_mode it doesn't matter if the letters are already in input_str:
    if not crossword_mode:
        invalid += input_str

    folder = f"hangman_solver/words/words_{language}"
    if language == "de" and not allow_umlauts:
        folder += "_only_a-z"

    if not os.path.isdir(folder):
        return {"error": "Invalid language."}

    return get_word_dict(input_str, [input_str], {"p": 1, "e": 1, "s": 1, "n": 1, "i": 1}, allow_umlauts, crossword_mode)


class HangmanSolver(RequestHandlerCustomError):
    def get(self, *args):
        words = find_words(self)

        if words.get("error"):
            self.write_error(400, exc_info=words.get("error"))
            return

        self.add_header("Content-Type", "text/html; charset=UTF-8")
        self.render("pages/hangman_solver.html", **words, url=get_url(self))


class HangmanSolverApi(RequestHandlerCustomError):
    def get(self, *args):
        words = find_words(self)

        self.add_header("Content-Type", "application/json")
        self.write(json.dumps(words))
