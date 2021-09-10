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

"""Config file for the page that swaps words."""
from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern
from typing import Optional, Tuple


class WordPair:
    """Class used to represent a word pair."""

    def get_replacement(self, word: str) -> str:  # pylint: disable=no-self-use
        """Get the replacement for a given word."""
        return word

    def to_pattern_str(self) -> str:  # pylint: disable=no-self-use
        """Get the pattern that matches the replaceable words."""
        return "a^"  # cannot match anything "a" followed by start of str

    def to_conf_line(
        self, len_of_left: Optional[int] = None
    ):  # pylint: disable=no-self-use, unused-argument
        """Get how this would look like in a config."""
        return ""

    def len_of_left(self) -> int:  # pylint: disable=no-self-use
        """Get the length to the left of the separator."""
        return 0


@dataclass
class Comment(WordPair):
    """Class used to represent a comment."""

    comment: str

    def to_conf_line(self, len_of_left: Optional[int] = None):
        """Get how this would look like in a config."""
        return f"# {self.comment}" if len(self.comment) > 0 else ""


@dataclass
class OneWayPair(WordPair):
    """Class used to represent a word that gets replaced with another."""

    word_regex: str
    replacement: str

    def get_replacement(self, word: str) -> str:
        """Get the replacement for a given word."""
        if re.fullmatch(self.word_regex, word) is not None:
            return self.replacement
        return word

    def to_pattern_str(self) -> str:
        """Get the pattern that matches the replaceable words."""
        return self.word_regex

    def to_conf_line(self, len_of_left: Optional[int] = None):
        """Get how this would look like in a config."""
        if len_of_left is None:
            filling_spaces = ""
        else:
            # the two spaces as default space between text an arrow
            filling_spaces = "  " + (" " * (len_of_left - self.len_of_left()))
        return (
            f"{self.word_regex}{filling_spaces}=>"
            f"{'' if len_of_left is None else ' '}{self.replacement}"
        )

    def len_of_left(self) -> int:
        """Get the length to the left of the separator."""
        return len(self.word_regex)


@dataclass
class TwoWayPair(WordPair):
    """Class used to represent two words that get replaced with each other."""

    word1: str
    word2: str

    def get_replacement(self, word: str) -> str:
        """Get the replacement for a given word."""
        if self.word1 == word:
            return self.word2
        if self.word2 == word:
            return self.word1
        return word

    def to_pattern_str(self) -> str:
        """Get the pattern that matches the replaceable words."""
        return f"{self.word1}|{self.word2}"

    def to_conf_line(self, len_of_left: Optional[int] = None):
        """Get how this would look like in a config."""
        if len_of_left is None:
            filling_spaces = ""
        else:
            # the one space as default space between text an arrow
            filling_spaces = " " + (" " * (len_of_left - self.len_of_left()))
        return (
            f"{self.word1}{filling_spaces}<=>"
            f"{'' if len_of_left is None else ' '}{self.word2}"
        )

    def len_of_left(self) -> int:
        """Get the length to the left of the separator."""
        return len(self.word1)


# mypy doesn't allow this with lowercase tuple
WORDS_TUPLE = Tuple[WordPair, ...]  # pylint: disable=invalid-name

LINE_END_REGEX: Pattern[str] = re.compile(
    r"[\n;]",  # ";" or new line
    re.MULTILINE,
)
COMMENT_LINE_REGEX: Pattern[str] = re.compile(
    r"#"  # the start of the comment
    r"\s*"  # optional white space
    r"("  # start of the group
    r"[^\s]"  # a non white space char (start of comment)
    r".*"  # whatever
    r")?"  # end group, make it optional, to allow lines with only #
)
LINE_REGEX: Pattern[str] = re.compile(
    r"\s*"  # white spaces to strip the word
    r"("  # start group one for the first word
    r"[^=\s()]"  # the start of the word, that can't contain white space
    r"[^=()]*"  # the middle of the word, that can't contain "="
    r"[^=\s<()]"  # the end of the word, that can't contain white space and "<"
    r")"  # end group one for the first word
    r"\s*"  # white spaces to strip the word
    r"(<?=>)"  # the seperator in the middle either "=>" or "<=>"
    r"\s*"  # white spaces to strip the word
    r"("  # start group two for the second word
    r"[^=\s>()]"  # the start of the word, that can't contain white space and >
    r"[^=()]*"  # the middle of the word, that can't contain "="
    r"[^=\s()]"  # the end of the word, that can't contain white space
    r")"  # end group two for the second word
    r"\s*"  # white spaces to strip the word
)


# pylint: disable=too-many-return-statements
def config_line_to_word_pair(line: str) -> Optional[WordPair]:
    """Parse one config line to one word pair instance."""
    if _m := re.fullmatch(COMMENT_LINE_REGEX, line):
        return Comment(_m.group(1))

    if len(line) == 0:
        return Comment("")  # empty comment → empty line

    _m = re.fullmatch(LINE_REGEX, line)
    if _m is None:
        return None

    left, right = _m.group(1), _m.group(3)
    if None in (left, right):
        return None

    left_re = re.compile(left)  # compile to make sure it doesn't break later

    separator = _m.group(2)
    if separator == "<=>":
        # compile to make sure it doesn't break later
        right_re = re.compile(right)
        return TwoWayPair(left_re.pattern, right_re.pattern)
    if separator == "=>":
        return OneWayPair(left_re.pattern, right)

    return None


def parse_config(config: str) -> WORDS_TUPLE:
    """Create a WORDS_TUPLE from a config str."""
    words_list: list[WordPair] = []
    for i, line in enumerate(re.split(LINE_END_REGEX, config.strip())):
        word_pair = config_line_to_word_pair(line)
        if word_pair is None:
            raise Exception(f"Line {i} ('{line}') is invalid.")
        words_list.append(word_pair)

    return tuple(words_list)


def words_to_regex(words: WORDS_TUPLE) -> Pattern[str]:
    """Get the words pattern that matches all words in words."""
    return re.compile(
        "|".join(
            tuple(f"({word_pair.to_pattern_str()})" for word_pair in words)
        ),
        re.IGNORECASE | re.UNICODE,
    )


def words_tuple_to_config(words: WORDS_TUPLE, minified: bool = False) -> str:
    """Create a readable config_str from a words tuple."""
    if minified:
        return ";".join(
            word_pair.to_conf_line()
            for word_pair in words
            if isinstance(word_pair, (OneWayPair, TwoWayPair))
        )
    max_len = max(word_pair.len_of_left() for word_pair in words)
    return "\n".join(word_pair.to_conf_line(max_len) for word_pair in words)


def minify(config: str) -> str:
    """Minify a config string."""
    return words_tuple_to_config(parse_config(config), True)


def beautify(config: str) -> str:
    """Beautify a config string."""
    return words_tuple_to_config(parse_config(config))
