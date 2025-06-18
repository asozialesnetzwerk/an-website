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

"""The tests for the swapped words page."""

from __future__ import annotations

from base64 import b64encode
from datetime import datetime

import orjson as json
import pytest
import regex
import tornado.web
import yaml
from time_machine import travel

from an_website.swapped_words import config_file as sw_config, swap

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_json_response,
    fetch,
)
from .test_settings import parse_cookie


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

    for string in (
        "abc def",
        "abc-def",
        "a b c d e f",
        "¯\\_(ツ)_/¯",
        "ab, cd.",
    ):
        lower = string.lower()
        upper = string.upper()
        title = string.title()
        for string in (  # pylint: disable=redefined-loop-name
            lower,
            upper,
            title,
        ):
            assert sw_config.copy_case(string, lower) == string
            assert sw_config.copy_case(string, upper) == string
            assert sw_config.copy_case(string, title) == string

    assert sw_config.copy_case("Long Short", "short LONG") == "Short Long"
    assert sw_config.copy_case("Test1 TEST2", "word1 word2") == "Word1 WORD2"


def test_parsing_config() -> None:
    """Test parsing the sw-config."""
    str_to_replace = "A a B b  XX  Cc cc cC CC  XX  Dd dd dD DD"

    test_conf_str = "(a)=>b;Cc<=>Dd"
    parsed_conf = sw_config.SwappedWordsConfig(test_conf_str)

    assert (  # pylint: disable=unnecessary-dunder-call
        parsed_conf.__eq__(None) == NotImplemented
    )
    beautified = parsed_conf.to_config_str()
    minified = parsed_conf.to_config_str(minified=True)

    assert minified == test_conf_str
    assert parsed_conf == sw_config.SwappedWordsConfig(beautified)
    assert (
        parsed_conf.swap_words(str_to_replace)
        == "B b B b  XX  Dd dd dD DD  XX  Cc cc cC CC"
    )
    assert regex.fullmatch(parsed_conf.get_regex(), "a")
    assert regex.fullmatch(parsed_conf.get_regex(), "cc")
    assert sw_config.beautify(minified) == beautified
    assert sw_config.minify(beautified) == minified
    assert parsed_conf.get_replacement_by_group_name("n", "lol") == "lol"
    assert parsed_conf.get_replacement_by_group_name("lol", "lol") == "lol"

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
    assert regex.fullmatch(parsed_conf.get_regex(), "a")
    assert regex.fullmatch(parsed_conf.get_regex(), "cc")
    assert sw_config.beautify(minified) == beautified
    assert sw_config.minify(beautified) == minified

    assert not sw_config.SwappedWordsConfig("").to_config_str()

    # test invalid configs
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


def test_two_way_word_pair() -> None:
    """Test the two-way word pair."""
    # pylint: disable=too-many-function-args
    pair = sw_config.TwoWayPair("x", "y")  # x <=> y
    assert pair.to_pattern_str() == "x|y"
    assert pair.get_replacement("x") == "y"
    assert pair.get_replacement("X") == "Y"
    assert pair.get_replacement("y") == "x"
    assert pair.get_replacement("Y") == "X"
    assert pair.get_replacement("z") == "z"
    assert pair.get_replacement("Z") == "Z"


def test_one_way_word_pair() -> None:
    """Test the one-way word pair."""
    # pylint: disable=too-many-function-args
    pair = sw_config.OneWayPair("x", "y")  # x => y
    assert pair.to_pattern_str() == "x"
    assert pair.get_replacement("x") == "y"
    assert pair.get_replacement("X") == "Y"
    assert pair.get_replacement("y") == "y"
    assert pair.get_replacement("Y") == "Y"
    assert pair.get_replacement("z") == "z"
    assert pair.get_replacement("Z") == "Z"


def test_check_text_too_long() -> None:
    """Test the check_text_too_long function."""
    swap.check_text_too_long("")
    swap.check_text_too_long("x" * swap.MAX_CHAR_COUNT)
    with pytest.raises(tornado.web.HTTPError):
        swap.check_text_too_long("x" * (swap.MAX_CHAR_COUNT + 1))


@travel(datetime(1, 2, 3, 4, 5, 6, 7), tick=False)
async def test_sw_html_request_handlers(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test the swapped words html request handlers."""
    assert_valid_html_response(
        await fetch(
            "/vertauschte-woerter",
            method="POST",
            body="reset=nope&text=" + "x" * (swap.MAX_CHAR_COUNT + 1),
        ),
        {413},  # text too long
    )
    assert_valid_html_response(
        await fetch(
            "/vertauschte-woerter",
            method="POST",
            body="",
        ),
        {400},  # missing argument
    )
    assert_valid_html_response(
        await fetch(
            "/vertauschte-woerter",
            method="POST",
            body="reset=nope&text=x&config=xyz",
        ),
        {400},  # invalid config
    )
    # everything ok
    assert_valid_html_response(
        await fetch(
            "/vertauschte-woerter",
            method="POST",
            body="reset=nope&text=x",
        ),
    )

    response = assert_valid_html_response(
        await fetch(
            "/vertauschte-woerter",
            method="POST",
            headers={"Content-Type": "application/yaml"},
            body=yaml.dump(
                {"reset": "nope", "text": "text", "config": "abc <=> xyz"}
            ),
        )
    )
    cookies = response.headers.get_list("Set-Cookie")
    assert len(cookies) == 1
    cookie = parse_cookie(cookies[0])
    morsel = cookie[tuple(cookie)[0]]
    assert morsel["expires"]
    assert morsel["path"] == "/vertauschte-woerter"
    assert morsel["samesite"] == "Strict"
    assert morsel.key == "swapped-words-config"
    assert morsel.value == b64encode(b"abc <=> xyz").decode("UTF-8")

    response2 = await fetch(
        "/vertauschte-woerter",
        method="POST",
        headers={"Content-Type": "application/json", "Cookie": cookies[0]},
        body=json.dumps(
            {
                "reset": "nope",
                "text": "text",
            }
        ),
    )
    assert not response2.headers.get_list("Set-Cookie")
    assert response2.body == response.body


async def test_sw_json_request_handlers(
    fetch: FetchCallable,  # noqa: F811
) -> None:
    """Test the swapped words JSON API request handlers."""
    response = assert_valid_json_response(
        await fetch(
            "/api/vertauschte-woerter",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "text": "x z o",
                    "config": "x  => y\nz <=> o",
                    "return_config": "sure",
                    "minify_config": "sure",
                }
            ),
        ),
    )
    assert response["text"] == "x z o"
    assert response["replaced_text"] == "y o z"
    assert response["return_config"] is True
    assert response["minify_config"] is True
    assert response["config"] == "x=>y;z<=>o"

    response = assert_valid_json_response(
        await fetch(
            "/api/vertauschte-woerter",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "text": "x y z",
                    "config": "# \n",
                    "return_config": "sure",
                    "minify_config": "nope",
                }
            ),
        ),
    )
    assert response["text"] == "x y z"
    assert response["replaced_text"] == "x y z"
    assert response["return_config"] is True
    assert response["minify_config"] is False
    # pylint: disable-next=use-implicit-booleaness-not-comparison-to-string
    assert response["config"] == ""

    response = assert_valid_json_response(
        await fetch(
            "/api/vertauschte-woerter",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "text": "x z o",
                    "config": "x  => y\nz <=> o",
                    "return_config": True,
                    "minify_config": False,
                }
            ),
        ),
    )
    assert response["text"] == "x z o"
    assert response["replaced_text"] == "y o z"
    assert response["return_config"] is True
    assert response["minify_config"] is False
    assert response["config"] == "x  => y\nz <=> o"

    response = assert_valid_json_response(
        await fetch(
            "/api/vertauschte-woerter",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "config": "x  => y\nz <> o",
                }
            ),
        ),
        {400},
    )
    assert response["line"] == "z <> o"
    assert response["line_num"] == 1

    response = assert_valid_json_response(
        await fetch(
            "/api/vertauschte-woerter",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "config": "x  => y\nz <=> o\na == b",
                }
            ),
        ),
        {400},
    )
    assert response["line"] == "a == b"
    assert response["line_num"] == 2


if __name__ == "__main__":
    test_copying_case_of_letters()
    test_copying_case()
    test_parsing_config()
    test_two_way_word_pair()
    test_one_way_word_pair()
    test_check_text_too_long()
