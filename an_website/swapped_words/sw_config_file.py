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
from re import Match, Pattern


def copy_case_letter(char_to_steal_case_from: str, char_to_change: str) -> str:
    """
    Copy the case of one string to another.

    This method assumes that the whole string has the same case, like it is
    the case for a letter.
    """
    return (
        char_to_change.upper()  # char_to_steal_case_from is upper case
        if char_to_steal_case_from.isupper()
        else char_to_change.lower()  # char_to_steal_case_from is lower case
    )


def copy_case(reference_word: str, word_to_change: str) -> str:
    """Copy the case of one string to another."""
    # lower case: "every letter is lower case"
    if reference_word.islower():
        return word_to_change.lower()
    # upper case: "EVERY LETTER IS UPPER CASE"
    if reference_word.isupper():
        return word_to_change.upper()
    # title case: "Every Word Begins With Upper Case Letter"
    if reference_word.istitle():
        return word_to_change.title()

    split_ref = reference_word.split(" ")
    split_word = word_to_change.split(" ")
    # if both equal length and not len == 1
    if len(split_ref) == len(split_word) != 1:
        # go over every word, if there are spaces
        return " ".join(
            copy_case(split_ref[i], split_word[i])
            for i in range(len(split_ref))
        )

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


class ConfigLine:  # pylint: disable=too-few-public-methods
    """Class used to represent a word pair."""

    def to_conf_line(  # pylint: disable=no-self-use, unused-argument
        self, len_of_left: None | int = None
    ) -> str:
        """Get how this would look like in a config."""
        return ""


@dataclass(frozen=True)
class Comment(ConfigLine):
    """Class used to represent a comment."""

    comment: str

    def to_conf_line(self, len_of_left: None | int = None) -> str:
        """Get how this would look like in a config."""
        return "" if not self.comment else f"# {self.comment}"


@dataclass(frozen=True, init=False)
class WordPair(ConfigLine):
    """Parent class representing a word pair."""

    word1: str
    word2: str
    # separator between the two words, that shouldn't be changed:
    separator: str = field(default="", init=False)

    def get_replacement(self, word: str) -> str:  # pylint: disable=no-self-use
        """Get the replacement for a given word with the same case."""
        return word

    def to_pattern_str(self) -> str:  # pylint: disable=no-self-use
        """Get the pattern that matches the replaceable words."""
        return "a^"  # cannot match anything "a" followed by start of str

    def len_of_left(self) -> int:
        """Get the length to the left of the separator."""
        return len(self.word1)

    def to_conf_line(self, len_of_left: None | int = None) -> str:
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
        if re.fullmatch(self.word1, word) is not None:
            return self.word2
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
        if self.word1 == word:
            return self.word2
        if self.word2 == word:
            return self.word1
        # Doesn't match case sensitive
        word_lower = word.lower()
        if self.word1.lower() == word_lower:
            return copy_case(word, self.word2)
        if self.word2.lower() == word_lower:
            return copy_case(word, self.word1)
        return word

    def to_pattern_str(self) -> str:
        """Get the pattern that matches the replaceable words."""
        return f"{self.word1}|{self.word2}"


WORDS_TUPLE = tuple[ConfigLine, ...]  # pylint: disable=invalid-name

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
    r"|[^\s<=>]?"  # one single letter word; optional -> better error message
    r")"  # end group one for the first word
    r"\s*"  # white spaces to strip the word
    r"(<?=>)"  # the seperator in the middle either "=>" or "<=>"
    r"\s*"  # white spaces to strip the word
    r"("  # start group two for the second word
    r"[^\s<=>]"  # the start of the word; can't contain: \s, "<", "=", ">"
    r"[^<=>]*"  # the middle of the word; can't contain: "<", "=", ">"
    r"[^\s<=>]"  # the end of the word; can't contain: \s, "<", "=", ">"
    r"|[^\s<=>]?"  # one single letter word; optional -> better error message
    r")"  # end group two for the second word
    r"\s*"  # white spaces to strip the word
)


@functools.lru_cache(maxsize=20)
def parse_config_line(  # noqa: C901  # pylint: disable=too-complex
    line: str, line_num: int = -1
) -> ConfigLine:
    """Parse one config line to one ConfigLine instance."""
    # remove white spaces to fix stuff, behaves weird otherwise
    line = line.strip()

    if not line:
        return Comment("")  # empty comment → empty line

    # print(len(line.strip()), f"'{line.strip()}'")

    if _m := re.fullmatch(COMMENT_LINE_REGEX, line):
        return Comment(_m.group(1))

    _m = re.fullmatch(LINE_REGEX, line)
    if _m is None:
        raise InvalidConfigError(line_num, line, "Line is invalid.")

    left, separator, right = _m.group(1), _m.group(2), _m.group(3)
    if not left:
        raise InvalidConfigError(line_num, line, "Left of separator is empty.")
    if separator not in ("<=>", "=>"):
        raise InvalidConfigError(
            line_num, line, "No separator ('<=>' or '=>') present."
        )
    if not right:
        raise InvalidConfigError(line_num, line, "Right of separator is empty.")

    try:
        # compile to make sure it doesn't break later
        left_re = re.compile(left)
    except re.error as _e:
        raise InvalidConfigError(
            line_num, line, f"Left is invalid regex: {_e}"
        ) from _e

    if separator == "<=>":
        try:
            # compile to make sure it doesn't break later
            right_re = re.compile(right)
        except re.error as _e:
            raise InvalidConfigError(
                line_num, line, f"Right is invalid regex: {_e}"
            ) from _e
        return TwoWayPair(left_re.pattern, right_re.pattern)
    if separator == "=>":
        return OneWayPair(left_re.pattern, right)

    raise InvalidConfigError(line_num, line, "Something went wrong.")


@dataclass(frozen=True)
class InvalidConfigError(Exception):
    """Exception raised if the config is invalid."""

    line_num: int
    line: str
    reason: str

    def __str__(self) -> str:
        """Exception to str."""
        return (
            f"Error in line {self.line_num}: '{self.line.strip()}' "
            f"with reason: {self.reason}"
        )


class SwappedWordsConfig:  # pylint: disable=eq-without-hash
    """SwappedWordsConfig class used to swap words in strings."""

    def __init__(self, config: str):
        """Parse a config string to a instance of this class."""
        self.lines: WORDS_TUPLE = tuple(
            parse_config_line(line, i)
            for i, line in enumerate(re.split(LINE_END_REGEX, config.strip()))
        )

    def get_regex(self) -> Pattern[str]:
        """Get the regex that matches every word in this."""
        return re.compile(
            "|".join(
                tuple(
                    f"(?P<n{i}>{word_pair.to_pattern_str()})"
                    for i, word_pair in enumerate(self.lines)
                    if isinstance(word_pair, WordPair)
                )
            ),
            re.IGNORECASE | re.UNICODE,
        )

    def to_config_str(self, minified: bool = False) -> str:
        """Create a readable config str from this."""
        if not self.lines:
            return ""
        if minified:
            return ";".join(
                word_pair.to_conf_line()
                for word_pair in self.lines
                if isinstance(word_pair, WordPair)
            )
        max_len = max(
            (
                word_pair.len_of_left()
                for word_pair in self.lines
                if isinstance(word_pair, WordPair)
            )
            or (0,)
        )
        return "\n".join(
            word_pair.to_conf_line(max_len) for word_pair in self.lines
        )

    def get_replacement_by_group_name(self, group_name: str, word: str) -> str:
        """Get the replacement of a word by the group name it matched."""
        if not group_name.startswith("n") or group_name == "n":
            return word
        index = int(group_name[1:])
        config_line = self.lines[index]
        if isinstance(config_line, WordPair):
            return config_line.get_replacement(word)

        return word

    def get_replaced_word(self, match: Match[str]) -> str:
        """Get the replaced word with the same case as the match."""
        for key, word in match.groupdict().items():
            if isinstance(word, str) and key.startswith("n"):
                return self.get_replacement_by_group_name(key, word)
        # if an unknown error happens return the match to change nothing:
        return match.group()

    def swap_words(self, text: str) -> str:
        """Swap the words in the text."""
        return self.get_regex().sub(self.get_replaced_word, text)

    def __eq__(self, other: object) -> bool:
        """Check equality based on the lines."""
        if not isinstance(other, SwappedWordsConfig):
            return NotImplemented
        return self.lines == other.lines


def minify(config: str) -> str:
    """Minify a config string."""
    return SwappedWordsConfig(config).to_config_str(True)


def beautify(config: str) -> str:
    """Beautify a config string."""
    return SwappedWordsConfig(config).to_config_str()
