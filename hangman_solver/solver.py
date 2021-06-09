from distutils.util import strtobool
import json

from utils.utils import get_url, RequestHandlerCustomError


def find_words(request_handler):
    input_str = request_handler.get_query_argument("input", default="")
    invalid = request_handler.get_query_argument("invalid", default="")
    allow_umlauts_str = request_handler.get_query_argument("has-umlauts", default="False")
    crossword_mode_str = request_handler.get_query_argument("crossword-mode", default="False")

    allow_umlauts = bool(strtobool(allow_umlauts_str))  # if the words can contain ä,ö,ü
    crossword_mode = bool(strtobool(crossword_mode_str))
    # in crossword_mode it doesn't matter if the letters are already in input_str:
    if not crossword_mode:
        invalid += input_str

    return {"input": input_str, "words": [input_str], "letters": {"p": 1, "e": 1, "s": 1, "n": 1, "i": 1}}


class HangmanSolver(RequestHandlerCustomError):
    def get(self, arg2):
        words = find_words(self)

        self.add_header("Content-Type", "text/html; charset=UTF-8")
        self.render("pages/hangman_solver.html", **words, url=get_url(self))


class HangmanSolverApi(RequestHandlerCustomError):
    def get(self, arg2):
        words = find_words(self)

        self.add_header("Content-Type", "application/json")
        self.write(json.dumps(words))
