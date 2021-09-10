# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Page that swaps words."""
from __future__ import annotations

from re import Match, Pattern
from typing import Optional

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import GIT_URL, ModuleInfo, PageInfo
from . import DIR
from .sw_config_file import WORDS_TUPLE, parse_config, words_to_regex


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
        keywords=("vertauschte", "Wörter", "witzig", "Känguru"),
        sub_pages=(
            PageInfo(
                name="Plugin",
                description="Ein Browser-Plugin, welches Wörter vertauscht.",
                path=f"{GIT_URL}/VertauschteWoerterPlugin/",
            ),
        ),
    )


# the max char code of the text to process.
MAX_CHAR_COUNT: int = 32768

with open(f"{DIR}/config.sw", encoding="utf-8") as file:
    DEFAULT_CONFIG: str = file.read()

WORDS: WORDS_TUPLE = parse_config(DEFAULT_CONFIG)

# create the WORDS_REGEX that matches every word in TO_SWAP
WORDS_REGEX: Pattern[str] = words_to_regex(WORDS)


def copy_case_letter(char_to_steal_case_from: str, char_to_change: str) -> str:
    """
    Copy the case of one string to another.

    This method assumes that the whole string has the same case, like it is
    the case for a letter.
    """
    return (
        char_to_change.upper()  # char_to_steal_case_from is upper case
        if char_to_steal_case_from.isupper()
        else char_to_change  # char_to_steal_case_from is lower case
    )


def copy_case(word_to_steal_case_from: str, word_to_change: str) -> str:
    """Copy the case of one string to another."""
    if len(word_to_change) == 1:
        # shouldn't happen, just to avoid future error with index of [1:]
        return copy_case_letter(word_to_steal_case_from[0], word_to_change)

    # word with only one upper case letter in beginning
    if (
        word_to_steal_case_from[0].isupper()
        and word_to_steal_case_from[1:].islower()
    ):
        return word_to_change[0].upper() + word_to_change[1:]

    # other words
    new_word: list[str] = []  # use list for speed
    for i, letter in enumerate(word_to_change):
        new_word.append(
            copy_case_letter(
                # overflow original word for mixed case
                word_to_steal_case_from[i % len(word_to_steal_case_from)],
                letter,
            )
        )

    # create new word and return it
    return "".join(new_word)


def swap_words(
    text: str,
    regex: Optional[Pattern[str]] = None,
    words: Optional[WORDS_TUPLE] = None,
) -> str:
    """Swap words with default options and with custom options."""
    swapped_once = swap_words_once(text, WORDS_REGEX, WORDS)
    if regex is None or words is None:
        # if one of them is None them, it can't be used
        return swapped_once

    return swap_words_once(swapped_once, regex, words)


def swap_words_once(text: str, regex: Pattern[str], words: WORDS_TUPLE) -> str:
    """Swap the words in the text."""

    def get_replaced_word_with_same_case(match: Match[str]) -> str:
        """Get the replaced word with the same case as the match."""
        for i, word in enumerate(match.groups()):
            if isinstance(word, str):  # word is not None
                # get the replacement from words
                replaced_word = words[i].get_replacement(word)
                return copy_case(word, replaced_word)  # copy the case

        # if an unknown error happens return the match to change nothing:
        return match.group()

    return regex.sub(get_replaced_word_with_same_case, text)


def check_text_too_long(text: str):
    """Raise an http error if the text is too long."""
    len_text = len(text)

    if len_text > MAX_CHAR_COUNT:
        raise HTTPError(
            413,
            reason=(
                f"The text has {len_text} characters, but it is only allowed "
                f"to have {MAX_CHAR_COUNT} characters. That's "
                f"{len_text - MAX_CHAR_COUNT} characters too much."
            ),
        )


class SwappedWords(BaseRequestHandler):
    """The request handler for the swapped words page."""

    def handle_text(self, text: str):
        """Use the text to display the html page."""
        check_text_too_long(text)

        self.render(
            "pages/swapped_words.html",
            text=text,
            output=swap_words(text),
            MAX_CHAR_COUNT=MAX_CHAR_COUNT,
        )

    def get(self):
        """Handle get requests to the swapped words page."""
        self.handle_text(self.get_query_argument("text", default=""))

    def post(self):
        """Handle post requests to the swapped words page."""
        self.handle_text(self.get_argument("text", default=""))


class SwappedWordsApi(APIRequestHandler):
    """The request handler for the swapped words api."""

    def get(self):
        """Handle get requests to the swapped words api."""
        text = self.get_argument("text", default="")

        check_text_too_long(text)

        self.finish({"replaced_text": swap_words(text)})
