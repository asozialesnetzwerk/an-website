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

"""The tests for the utils module."""

from urllib.parse import urlsplit

import pytest

from an_website.utils import utils


def test_adding_stuff_to_url() -> None:
    """Test the utils.add_args_to_url function."""
    for url in (
        "https://example.com/",
        "https://example.com/?a=b&b=c",
        "https://example.com/?x=z",
    ):
        assert url == utils.add_args_to_url(url)
        assert "x=y" in urlsplit(utils.add_args_to_url(url, x="y")).query

    assert (
        urlsplit(
            utils.add_args_to_url("https://example.com/", a="b", c="d", e="f")
        ).query
        == "a=b&c=d&e=f"
    )

    assert (
        utils.add_args_to_url("https://example.com/", a="b", c="d", e=True)
        == f"https://example.com/?a=b&c=d&e={utils.bool_to_str(True)}"
    )

    assert (
        f"a={utils.bool_to_str(True)}"
        == urlsplit(utils.add_args_to_url("https://example.com/", a=True)).query
    )


def test_anonomyze_ip() -> None:
    """Test the anonomyze_ip function."""
    assert utils.anonymize_ip("10.88.135.144") == "10.88.135.0"
    assert (
        utils.anonymize_ip("2001:db8:85a3::8a2e:370:7334") == "2001:db8:85a3::"
    )
    with pytest.raises(ValueError):
        utils.anonymize_ip("invalid")
    assert utils.anonymize_ip("invalid", ignore_invalid=True) == "invalid"


def test_bool_str_conversion() -> None:
    """Test the conversion from bool to str and from str to bool."""
    for boolean in (False, True):
        assert boolean is utils.str_to_bool(utils.bool_to_str(boolean))
        assert boolean is utils.str_to_bool(str(boolean))

    for boolean_str in ("sure", "nope"):
        boolean_bool = utils.str_to_bool(boolean_str)
        assert isinstance(boolean_bool, bool)
        assert boolean_str == utils.bool_to_str(boolean_bool)

    with pytest.raises(ValueError):
        utils.str_to_bool("Invalid bool value")

    assert utils.str_to_bool("Invalid bool value", True) is True


def test_country_code_to_flag() -> None:
    """Test the utils.country_code_to_flag function."""
    assert utils.country_code_to_flag("aq") == "🇦🇶"
    assert utils.country_code_to_flag("aQ") == "🇦🇶"
    assert utils.country_code_to_flag("Aq") == "🇦🇶"
    assert utils.country_code_to_flag("AQ") == "🇦🇶"


def test_n_from_set() -> None:
    """Test the n_from_set function."""
    set_ = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    assert len(utils.n_from_set(set_, 3)) == 3
    assert -1 < len(utils.n_from_set(set_, 0)) < 1
    assert -1 < len(utils.n_from_set(set_, -1)) < 1
    for element in utils.n_from_set(set_, 8):
        assert element in set_
    for i in range(len(set_) + 3):
        assert len(utils.n_from_set(set_, i)) == min(len(set_), i)


def test_name_to_id() -> None:
    """Test the name_to_id function."""
    assert utils.name_to_id("     test 42069     ") == "test-42069"
    assert utils.name_to_id("     test-test-42069") == "test-test-42069"
    assert utils.name_to_id("     test_TEST_42069") == "test-test-42069"
    assert utils.name_to_id("     test test 42069") == "test-test-42069"
    assert utils.name_to_id("test__  __TEST_42069") == "test-test-42069"
    assert utils.name_to_id("test test test 42069") == "test-test-test-42069"
    assert utils.name_to_id("TEST test_test_42069") == "test-test-test-42069"
    assert utils.name_to_id("ẞ Ä Ö Ü-ẞÄÖÜ        ") == "ss-ae-oe-ue-ssaeoeue"


def test_replace_umlauts() -> None:
    """Test the replace_umlauts function."""
    assert utils.replace_umlauts("äöüß") == "aeoeuess"
    assert utils.replace_umlauts("ÄÖÜẞ") == "AEOEUESS"
    assert utils.replace_umlauts("Äöüß") == "Aeoeuess"
    assert utils.replace_umlauts("Öäüß") == "Oeaeuess"
    assert utils.replace_umlauts("Üöäß") == "Ueoeaess"
    assert utils.replace_umlauts("ẞäöü") == "SSaeoeue"
    assert utils.replace_umlauts("ẞäöü ÄÖÜẞ") == "SSaeoeue AEOEUESS"
    assert utils.replace_umlauts("ẞäöü ÄÖÜß") == "SSaeoeue AeOeUess"
    assert utils.replace_umlauts("ẞÄÖÜ ÄöÜß") == "SSAEOEUE AeoeUess"


def test_time_to_str() -> None:
    """Test the time_to_str function."""
    assert utils.time_to_str(0) == "0d 0h 0min 0s"
    assert utils.time_to_str(133769420) == "1548d 6h 10min 20s"


def test_get_close_matches() -> None:
    """Test the get_close_matches function."""
    assert utils.get_close_matches("a", ("a", "b"), cutoff=0) == ("a",)
    assert utils.get_close_matches("", ("a", "b"), cutoff=1.0) == ("a", "b")
    assert utils.get_close_matches("aa", ("ab", "baa", "acab")) == (
        "baa",
        "ab",
        "acab",
    )
    assert utils.get_close_matches("ab", "bcdefghiajklmnop") == ("a", "b")
    assert utils.get_close_matches("a", "awawawawawawawawawawawa", 1) == ("a",)
    assert utils.get_close_matches("a𓆗", "a") == ("a",)


if __name__ == "__main__":
    test_adding_stuff_to_url()
    test_anonomyze_ip()
    test_bool_str_conversion()
    test_country_code_to_flag()
    test_n_from_set()
    test_name_to_id()
    test_replace_umlauts()
    test_time_to_str()
    test_get_close_matches()
