"""Page that swaps words."""
from __future__ import annotations

import re
from re import Match, Pattern

from tornado.web import HTTPError

from ..utils.utils import (
    GIT_URL,
    APIRequestHandler,
    BaseRequestHandler,
    ModuleInfo,
    PageInfo,
)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/vertauschte-woerter/?", SwappedWords),
            (r"/swapped-words/?", SwappedWords),
            (r"/vertauschte-woerter/api", SwappedWordsApi),
            (r"/swapped-words/api", SwappedWordsApi),
        ),
        name="Vertauschte Wörter",
        description="Eine Seite, die Wörter vertauscht",
        path="/vertauschte-woerter",
        sub_pages=(
            PageInfo(
                "Plugin",
                "Ein Browser-Plugin, welches Wörter vertauscht.",
                f"{GIT_URL}/VertauschteWoerterPlugin/",
            ),
        ),
    )


# the max char code of the text to process.
MAX_CHAR_COUNT: int = 32768

TO_SWAP: dict[str, str] = {
    "amüsant": "relevant",
    "amüsanz": "relevanz",
    "ministerium": "mysterium",
    "ministerien": "mysterien",
    "bundestag": "schützenverein",
    "ironisch": "erotisch",
    "ironien": "erotiken",
    "ironie": "erotik",
    "ironiker": "erotiker",
    "problem": "ekzem",
    "kritisch": "kryptisch",
    "kritik": "kryptik",
    "provozier": "produzier",
    "arbeitnehmer": "arbeitgeber",
    "arbeitsnehmer": "arbeitsgeber",
}

words: list[str] = []

for _w1, _w2 in tuple(TO_SWAP.items()):
    TO_SWAP[_w2] = _w1
    words.append(_w1)
    words.append(_w2)

WORDS_REGEX: Pattern[str] = re.compile(
    "(" + "|".join(words) + ")", re.IGNORECASE
)
del words


def get_replaced_word_with_same_case(match: Match[str]) -> str:
    """Get the replaced word with the same case as the match."""
    word = match.group()
    replaced_word = TO_SWAP.get(word.lower(), word)

    if word == replaced_word:
        return word

    if word.isupper():
        return replaced_word.upper()

    if word[0].isupper():
        return replaced_word[0].upper() + replaced_word[1:]

    # is probably lower
    return replaced_word


def swap_words(text: str) -> str:
    """Swap the words in the text."""
    test = WORDS_REGEX.sub(get_replaced_word_with_same_case, text)
    return test


def get_text_too_long_error_message(len_of_text: int) -> str:
    """Get the error message for a text that is too long."""
    return (
        f"The text has {len_of_text} characters, but it is only allowed "
        f"to have {MAX_CHAR_COUNT} characters. That's "
        f"{len_of_text-MAX_CHAR_COUNT} characters too much."
    )


class SwappedWords(BaseRequestHandler):
    """The request handler for the swapped words page."""

    def get(self):
        """Handle get requests to the swapped words page."""
        text = self.get_query_argument("text", default="")
        len_text = len(text)

        if len_text > MAX_CHAR_COUNT:
            raise HTTPError(
                413, reason=get_text_too_long_error_message(len_text)
            )

        self.render(
            "pages/swapped_words.html",
            text=text,
            output=swap_words(text),
            MAX_CHAR_COUNT=MAX_CHAR_COUNT,
        )


class SwappedWordsApi(APIRequestHandler):
    """The request handler for the swapped words api."""

    def get(self):
        """Handle get requests to the swapped words api."""
        text = self.get_argument("text", default="")

        len_text = len(text)

        if len_text > MAX_CHAR_COUNT:
            raise HTTPError(
                413, reason=get_text_too_long_error_message(len_text)
            )

        replaced_text = swap_words(text)

        self.finish({"replaced_text": replaced_text})
