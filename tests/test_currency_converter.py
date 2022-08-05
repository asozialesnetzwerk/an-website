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

"""The tests for the currency converter."""

from __future__ import annotations

import asyncio

from an_website.currency_converter import converter


def test_num_string_conversion() -> None:
    """Test the num_to_string and string_to_num conversion."""
    for num_str in ("0,50", "0,75", "1", "5,50", "10", "100"):
        _num: int = converter.string_to_num(num_str)
        assert converter.num_to_string(_num) == num_str

    assert converter.string_to_num("1,50") == 150
    assert converter.string_to_num("100xx") == 100 * 100
    assert converter.string_to_num("1,,50") == 150
    assert converter.string_to_num("100,,,,,,") == 100 * 100
    assert converter.string_to_num("1,50") == 150

    assert converter.num_to_string(150) == "1,50"
    assert converter.num_to_string(10000) == "100"

    for not_a_num in ("", ".", "..", "text"):
        assert not converter.string_to_num(not_a_num)


async def test_currency_conversion() -> None:
    """Test the currency conversion."""
    for _f in (0.5, 1, 2, 4, 8, 16, 32, 64, 128):
        val_dict = await converter.get_value_dict(int(_f * 100))
        for currency in ("euro", "mark", "ost", "schwarz"):
            assert val_dict[currency] == converter.string_to_num(
                val_dict[f"{currency}_str"]  # type: ignore[arg-type]
            )
            assert val_dict[f"{currency}_str"] == converter.num_to_string(
                val_dict[currency]  # type: ignore[arg-type]
            )
            assert str(val_dict[f"{currency}_str"]) in str(val_dict["text"])
    assert converter.convert(1) == (1, 2, 4, 20)
    assert converter.convert(2) == (2, 4, 8, 40)


if __name__ == "__main__":
    test_num_string_conversion()
    asyncio.run(test_currency_conversion())
