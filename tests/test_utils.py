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

from an_website.utils import utils


def test_n_from_set():
    """Test the n_from_set function."""
    _set = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    assert len(utils.n_from_set(_set, 3)) == 3
    for i in range(len(_set) + 3):
        assert len(utils.n_from_set(_set, i)) == min(len(_set), i)


if __name__ == "__main__":
    test_n_from_set()
