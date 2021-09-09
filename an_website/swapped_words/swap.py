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

import re
from re import Match, Pattern

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import GIT_URL, ModuleInfo, PageInfo


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

# add the elements to TO_SWAP in reverse as well
for _w1, _w2 in tuple(TO_SWAP.items()):
    TO_SWAP[_w2] = _w1

del _w1, _w2

# create the WORDS_REGEX that matches every word in TO_SWAP
WORDS_REGEX: Pattern[str] = re.compile(
    "(" + "|".join(TO_SWAP.keys()) + ")", re.IGNORECASE
)


def copy_case(char_to_steal_case_from: str, char_to_change: str) -> str:
    """Copy the case of one char to another."""
    return (
        char_to_change.upper()  # char_to_steal_case_from is upper case
        if char_to_steal_case_from.isupper()
        else char_to_change  # char_to_steal_case_from is lower case
    )


def get_replaced_word_with_same_case(match: Match[str]) -> str:
    """Get the replaced word with the same case as the match."""
    word = match.group()
    replaced_word = TO_SWAP.get(word.lower(), word)

    if len(replaced_word) == 1:
        # shouldn't happen, just to avoid future error with index of [1:]
        return copy_case(word[0], replaced_word)

    # word with only one upper case letter in beginning
    if word[0].isupper() and word[1:].islower():
        return replaced_word[0].upper() + replaced_word[1:]

    # other words
    new_word: list[str] = []  # use list for speed
    for i, letter in enumerate(replaced_word):
        new_word.append(
            copy_case(
                word[i % len(word)],  # overflow original word for mixed case
                letter,
            )
        )

    # create new word and return it
    return "".join(new_word)


def swap_words(text: str) -> str:
    """Swap the words in the text."""
    return WORDS_REGEX.sub(get_replaced_word_with_same_case, text)


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
