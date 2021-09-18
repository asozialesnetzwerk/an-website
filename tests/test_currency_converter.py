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

"""The module with all the tests for the currency_converter module."""

from __future__ import annotations

import asyncio

from an_website.currency_converter import converter


def test_num_string_conversion():
    """Test the num_to_string and string_to_num conversion."""
    for num in (0.5, 0.75, 1, 5.5, 10, 100):
        assert converter.string_to_num(converter.num_to_string(num)) == num
        assert (
            converter.string_to_num(converter.num_to_string(num), divide_by=20)
            == num / 20
        )
        assert converter.string_to_num(str(num)) == num

    for num in ("0,50", "0,75", "1", "5,50", "10", "100"):
        assert converter.num_to_string(converter.string_to_num(num)) == num

    assert converter.string_to_num("1,50") == 1.5
    assert converter.string_to_num("100") == 100

    assert converter.num_to_string(1.5) == "1,50"
    assert converter.num_to_string(100) == "100"

    for not_a_num in ("", None, ".", "..", "text"):
        assert converter.string_to_num(not_a_num) is None


def test_currency_conversion():
    """Test the currency conversion."""
    for _f in (0.5, 1, 2, 4, 8, 16, 32, 64, 128):
        val_dict = asyncio.run(converter.get_value_dict(_f))
        for currency in ("euro", "mark", "ost", "schwarz"):
            assert val_dict[currency] == converter.string_to_num(
                val_dict[f"{currency}_str"]
            )
            assert val_dict[f"{currency}_str"] == converter.num_to_string(
                val_dict[currency]
            )
            assert val_dict[f"{currency}_str"] in val_dict["text"]


if __name__ == "__main__":
    test_num_string_conversion()
    test_currency_conversion()
