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

"""The module with all the tests for the utils module."""

from __future__ import annotations

from urllib.parse import urlparse

import pytest

from an_website.utils import utils


def test_n_from_set() -> None:
    """Test the n_from_set function."""
    _set = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    assert len(utils.n_from_set(_set, 3)) == 3
    assert -1 < len(utils.n_from_set(_set, 0)) < 1
    assert -1 < len(utils.n_from_set(_set, -1)) < 1
    for _el in utils.n_from_set(_set, 8):
        assert _el in _set
    for i in range(len(_set) + 3):
        assert len(utils.n_from_set(_set, i)) == min(len(_set), i)


def test_bool_str_conversion() -> None:
    """Test the conversion from bool to str and from str to bool."""
    for _b in (False, True):
        assert _b == utils.str_to_bool(utils.bool_to_str(_b))
        assert _b == utils.str_to_bool(str(_b))

    for _b_str in ("sure", "nope"):
        _b_bool = utils.str_to_bool(_b_str)
        assert isinstance(_b_bool, bool)
        assert _b_str == utils.bool_to_str(_b_bool)

    with pytest.raises(ValueError):
        utils.str_to_bool("Invalid bool value")

    assert utils.str_to_bool("Invalid bool value", default=True)


def test_adding_stuff_to_url() -> None:
    """Test the utils.add_args_to_url function."""
    for url in (
        "https://example.com/",
        "https://example.com/?a=b&b=c",
        "https://example.com/?x=z",
    ):
        assert url == utils.add_args_to_url(url)
        assert "x=y" in urlparse(utils.add_args_to_url(url, x="y")).query

    assert (
        urlparse(
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
        == urlparse(utils.add_args_to_url("https://example.com/", a=True)).query
    )


def test_anonomyze_ip() -> None:
    """Test the anonomyze_ip function."""
    assert utils.anonymize_ip("127.0.0.1") == "127.0.0.0"
    assert utils.anonymize_ip("127.0.0.1", ignore_invalid=True) == "127.0.0.0"
    assert utils.anonymize_ip("69.69.69.69") == "69.69.69.0"
    assert utils.anonymize_ip("69.6.9.69", ignore_invalid=True) == "69.6.9.0"
    assert utils.anonymize_ip("invalid", ignore_invalid=True) == "invalid"

    with pytest.raises(ValueError):
        utils.anonymize_ip("invalid")


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


if __name__ == "__main__":
    test_n_from_set()
    test_bool_str_conversion()
    test_adding_stuff_to_url()
    test_anonomyze_ip()
    test_replace_umlauts()
    test_name_to_id()
