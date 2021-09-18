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

import functools
import re
from dataclasses import dataclass, field
from re import Pattern
from typing import Optional, Tuple, Union


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


def copy_case(reference_word: str, word_to_change: str) -> str:
    """Copy the case of one string to another."""
    if len(word_to_change) == 1:
        # shouldn't happen, just to avoid future error with index of [1:]
        return copy_case_letter(reference_word[0], word_to_change)

    split_ref = reference_word.split(" ")
    split_word = word_to_change.split(" ")
    # if both equal length and not len == 1
    if len(split_ref) == len(split_word) != 1:
        return " ".join(
            copy_case(split_ref[i], split_word[i])
            for i in range(len(split_ref))
        )

    # word with only one upper case letter in beginning
    if reference_word[0].isupper() and reference_word[1:].islower():
        return word_to_change[0].upper() + word_to_change[1:]

    # other words
    new_word: list[str] = []  # use list for speed
    for i, letter in enumerate(word_to_change):
        new_word.append(
            copy_case_letter(
                # overflow original word for mixed case
                reference_word[i % len(reference_word)],
                letter,
            )
        )

    # create new word and return it
    return "".join(new_word)


class ConfigLine:
    """Class used to represent a word pair."""

    def get_replacement(self, word: str) -> str:  # pylint: disable=no-self-use
        """Get the replacement for a given word with the same case."""
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
        """
        Get the length to the left of the separator.

        Only used for word pairs.
        """
        return 0


@dataclass(frozen=True)
class Comment(ConfigLine):
    """Class used to represent a comment."""

    comment: str

    def to_conf_line(self, len_of_left: Optional[int] = None):
        """Get how this would look like in a config."""
        return (
            ""
            if self.comment is None or len(self.comment) == 0
            else f"# {self.comment}"
        )


@dataclass(frozen=True, init=False)
class WordPair(ConfigLine):
    """Parent class representing a word pair."""

    word1: str
    word2: str
    # separator between the two words, that shouldn't be changed:
    separator: str = field(default="", init=False)

    def len_of_left(self) -> int:
        """Get the length to the left of the separator."""
        return len(self.word1)

    def to_conf_line(self, len_of_left: Optional[int] = None):
        """Get how this would look like in a config."""
        left, separator, right = self.word1, self.separator, self.word2
        if len_of_left is None:
            return "".join((left, separator.strip(), right))
        return (
            left
            + (" " * (1 + len_of_left - self.len_of_left()))
            + separator
            + " "
            + right
        )


@dataclass(frozen=True)
class OneWayPair(WordPair):
    """Class used to represent a word that gets replaced with another."""

    # separator between the two words, that shouldn't be changed:
    separator: str = field(default=" =>", init=False)

    def get_replacement(self, word: str) -> str:
        """Get the replacement for a given word with the same case."""
        _re_word1 = re.compile(self.word1, re.IGNORECASE)
        if re.fullmatch(_re_word1, word) is not None:
            return copy_case(word, self.word2)
        return word

    def to_pattern_str(self) -> str:
        """Get the pattern that matches the replaceable words."""
        return self.word1


@dataclass(frozen=True)
class TwoWayPair(WordPair):
    """Class used to represent two words that get replaced with each other."""

    # separator between the two words, that shouldn't be changed:
    separator: str = field(default="<=>", init=False)

    def get_replacement(self, word: str) -> str:
        """Get the replacement for a given word with the same case."""
        word_lower = word.lower()
        if self.word1.lower() == word_lower:
            return copy_case(word, self.word2)
        if self.word2.lower() == word_lower:
            return copy_case(word, self.word1)
        return word

    def to_pattern_str(self) -> str:
        """Get the pattern that matches the replaceable words."""
        return f"{self.word1}|{self.word2}"


# mypy doesn't allow this with lowercase tuple
WORDS_TUPLE = Tuple[ConfigLine, ...]  # pylint: disable=invalid-name

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
    r"[^\s<=>]"  # the start of the word; can't contain: \s, "<", "=", ">"
    r"[^<=>]*"  # the middle of the word; can't contain: "<", "=", ">"="
    r"[^\s<=>]"  # the end of the word; can't contain: \s, "<", "=", ">"
    r")?"  # end group one for the first word
    r"\s*"  # white spaces to strip the word
    r"(<?=>)?"  # the seperator in the middle either "=>" or "<=>"
    r"\s*"  # white spaces to strip the word
    r"("  # start group two for the second word
    r"[^\s<=>]"  # the start of the word; can't contain: \s, "<", "=", ">"
    r"[^<=>]*"  # the middle of the word; can't contain: "<", "=", ">"
    r"[^\s<=>]"  # the end of the word; can't contain: \s, "<", "=", ">"
    r")?"  # end group two for the second word
    r"\s*"  # white spaces to strip the word
)


# pylint: disable=too-many-return-statements
@functools.lru_cache(maxsize=20)
def config_line_to_word_pair(  # noqa: C901
    line: str,
) -> Union[str, ConfigLine]:
    """Parse one config line to one word pair instance."""
    # remove white spaces to fix stuff, behaves weird otherwise
    line = line.strip()

    if len(line) == 0:
        return Comment("")  # empty comment → empty line

    # print(len(line.strip()), f"'{line.strip()}'")

    if _m := re.fullmatch(COMMENT_LINE_REGEX, line):
        return Comment(_m.group(1))

    _m = re.fullmatch(LINE_REGEX, line)
    if _m is None:
        return "Line is invalid."

    left, separator, right = _m.group(1), _m.group(2), _m.group(3)
    if left is None:
        return "Left of separator is empty."
    if separator not in ("<=>", "=>"):
        return "No separator ('<=>' or '=>') present."
    if right is None:
        return "Right of separator is empty."

    try:
        # compile to make sure it doesn't break later
        left_re = re.compile(left)
    except re.error as _e:
        return f"Left is invalid: {_e}"

    if separator == "<=>":
        try:
            # compile to make sure it doesn't break later
            right_re = re.compile(right)
        except re.error as _e:
            return f"Right is invalid: {_e}"
        return TwoWayPair(left_re.pattern, right_re.pattern)
    if separator == "=>":
        return OneWayPair(left_re.pattern, right)

    return "Something went wrong."


@dataclass(frozen=True)
class InvalidConfigException(Exception):
    """Exception thrown if the config is invalid."""

    line_num: int
    line: str
    reason: str

    def __str__(self):
        """Exception to str."""
        return (
            f"Error in line {self.line_num}: '{self.line.strip()}' "
            f"with reason: {self.reason}"
        )


@functools.lru_cache(maxsize=20)
def parse_config(config: str, throw_exception: bool = True) -> WORDS_TUPLE:
    """Create a WORDS_TUPLE from a config str."""
    words_list: list[ConfigLine] = []
    for i, line in enumerate(re.split(LINE_END_REGEX, config.strip())):
        word_pair = config_line_to_word_pair(line)
        if isinstance(word_pair, ConfigLine):
            words_list.append(word_pair)
        elif throw_exception:
            raise InvalidConfigException(i, line, reason=word_pair)

    return tuple(words_list)


@functools.lru_cache(maxsize=20)
def words_to_regex(words: WORDS_TUPLE) -> Pattern[str]:
    """Get the words pattern that matches all words in words."""
    return re.compile(
        "|".join(
            tuple(
                f"(?P<n{i}>{word_pair.to_pattern_str()})"
                for i, word_pair in enumerate(words)
                if isinstance(word_pair, WordPair)
            )
        ),
        re.IGNORECASE | re.UNICODE,
    )


@functools.lru_cache(maxsize=20)
def words_tuple_to_config(words: WORDS_TUPLE, minified: bool = False) -> str:
    """Create a readable config_str from a words tuple."""
    if minified:
        return ";".join(
            word_pair.to_conf_line()
            for word_pair in words
            if isinstance(word_pair, WordPair)
        )
    max_len = max(word_pair.len_of_left() for word_pair in words)
    return "\n".join(word_pair.to_conf_line(max_len) for word_pair in words)


def minify(config: str) -> str:
    """Minify a config string."""
    return words_tuple_to_config(parse_config(config), True)


def beautify(config: str) -> str:
    """Beautify a config string."""
    return words_tuple_to_config(parse_config(config))
