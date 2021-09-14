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

from an_website.currency_converter import converter


def test_num_string_conversion():
    for num in (0.5, 0.75, 1, 5.5, 10, 100):
        assert converter.string_to_num(converter.num_to_string(num)) == num
        assert converter.string_to_num(
            converter.num_to_string(num), divide_by=20
        ) == num/20

    for num in ("0,50", "0,75", "1", "5,50", "10", "100"):
        assert converter.num_to_string(converter.string_to_num(num)) == num

    assert converter.string_to_num("1,50") == 1.5
    assert converter.string_to_num("100") == 100

    assert converter.num_to_string(1.5) == "1,50"
    assert converter.num_to_string(100) == "100"


def do_tests():
    test_num_string_conversion()


if __name__ == '__main__':
    do_tests()

