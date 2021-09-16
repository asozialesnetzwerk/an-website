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

import pytest
from tornado.httputil import urlparse

from an_website.utils import utils


def test_n_from_set():
    """Test the n_from_set function."""
    _set = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    assert len(utils.n_from_set(_set, 3)) == 3
    for i in range(len(_set) + 3):
        assert len(utils.n_from_set(_set, i)) == min(len(_set), i)


def test_bool_str_conversion():
    """Test the conversion from bool to str and from str to bool."""
    for _b in (False, True):
        assert _b == utils.str_to_bool(utils.bool_to_str(_b))
        assert _b == utils.str_to_bool(str(_b))

    for _b in ("sure", "nope"):
        assert _b == utils.bool_to_str(utils.str_to_bool(_b))

    with pytest.raises(ValueError):
        utils.str_to_bool("Invalid bool value")

    assert utils.str_to_bool("Invalid bool value", default=True)


def test_adding_stuff_to_url():
    """Test the utils.add_args_to_url function."""
    for url in (
        "https://example.com/",
        "https://example.com/?a=b&b=c",
        "https://example.com/?x=z",
    ):
        assert url == utils.add_args_to_url(url)
        assert "x=y" in urlparse(utils.add_args_to_url(url, x="y")).query

    assert (
        "a=b&c=d&e=f"
        == urlparse(
            utils.add_args_to_url("https://example.com/", a="b", c="d", e="f")
        ).query
    )

    assert (
        f"a={utils.bool_to_str(True)}"
        == urlparse(
            utils.add_args_to_url("https://example.com/", a=True)
        ).query
    )


if __name__ == "__main__":
    test_n_from_set()
    test_bool_str_conversion()
    test_adding_stuff_to_url()
