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

"""Tests for the swapped_words module."""
from __future__ import annotations

import re

import pytest

from an_website.swapped_words import sw_config_file as sw_config


def test_copying_case_of_letters() -> None:
    """Test the copying of cases for single letters."""
    lower_char = "a"
    upper_char = "A"
    for _c1, _c2 in (
        (lower_char, lower_char),
        (lower_char, upper_char),
        (upper_char, upper_char),
        (upper_char, lower_char),
    ):
        assert sw_config.copy_case_letter(_c1, _c2) == _c1

    for char in ("a", "B", "c", "D", "e", "F", "g", "H"):
        assert sw_config.copy_case_letter(char, "a").isupper() == char.isupper()
        assert sw_config.copy_case_letter(char, char.lower()) == char


def test_copying_case() -> None:
    """Test the copying of cases for strings."""
    for word in ("lower", "Upper", "CAPS", "AlTeRnAtInG", "lasT", "AHh!1!1!!"):
        assert sw_config.copy_case(word, word.lower()) == word
        assert sw_config.copy_case(word, word.upper()) == word
        assert sw_config.copy_case(word, word.title()) == word

    for _str in ("abc def", "abc-def", "a b c d e f", "¯\\_(ツ)_/¯", "ab, cd."):
        lower = _str.lower()
        upper = _str.upper()
        title = _str.title()
        for _str2 in (lower, upper, title):
            assert sw_config.copy_case(_str2, lower) == _str2
            assert sw_config.copy_case(_str2, upper) == _str2
            assert sw_config.copy_case(_str2, title) == _str2

    assert sw_config.copy_case("Long Short", "short LONG") == "Short Long"


def test_parsing_config() -> None:
    """Test parsing the sw-config."""
    str_to_replace = "A a B b  XX  Cc cc cC CC  XX  Dd dd dD DD"

    test_conf_str = "(a)=>b;Cc<=>Dd"
    parsed_conf = sw_config.SwappedWordsConfig(test_conf_str)

    beautified = parsed_conf.to_config_str()
    minified = parsed_conf.to_config_str(minified=True)

    assert minified == test_conf_str
    assert parsed_conf == sw_config.SwappedWordsConfig(beautified)
    assert (
        parsed_conf.swap_words(str_to_replace)
        == "B b B b  XX  Dd dd dD DD  XX  Cc cc cC CC"
    )
    assert re.fullmatch(parsed_conf.get_regex(), "a")
    assert re.fullmatch(parsed_conf.get_regex(), "cc")
    assert sw_config.beautify(minified) == beautified
    assert sw_config.minify(beautified) == minified

    test_conf_str = "a  <=> b\nCc  => Dd"
    parsed_conf = sw_config.SwappedWordsConfig(test_conf_str)

    beautified = parsed_conf.to_config_str()
    minified = parsed_conf.to_config_str(minified=True)

    assert beautified == test_conf_str
    assert parsed_conf == sw_config.SwappedWordsConfig(minified)
    assert (
        parsed_conf.swap_words(str_to_replace)
        == "B b A a  XX  Dd dd dD DD  XX  Dd dd dD DD"
    )
    assert re.fullmatch(parsed_conf.get_regex(), "a")
    assert re.fullmatch(parsed_conf.get_regex(), "cc")
    assert sw_config.beautify(minified) == beautified
    assert sw_config.minify(beautified) == minified

    # test invalid configs:
    with pytest.raises(sw_config.InvalidConfigError):
        sw_config.SwappedWordsConfig(" <=> b")

    with pytest.raises(sw_config.InvalidConfigError):
        sw_config.SwappedWordsConfig("a <=> ")

    with pytest.raises(sw_config.InvalidConfigError):
        sw_config.SwappedWordsConfig("a <> b")

    with pytest.raises(sw_config.InvalidConfigError):
        sw_config.SwappedWordsConfig("a <= b")

    with pytest.raises(sw_config.InvalidConfigError):
        sw_config.SwappedWordsConfig("a( => b")

    with pytest.raises(sw_config.InvalidConfigError):
        sw_config.SwappedWordsConfig("a <=> (b")

    try:
        sw_config.SwappedWordsConfig("a <=> (b")
    except sw_config.InvalidConfigError as exc:
        assert exc.reason in str(exc)


if __name__ == "__main__":
    test_copying_case_of_letters()
    test_copying_case()
    test_parsing_config()
