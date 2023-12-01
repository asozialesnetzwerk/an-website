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

"""The tests for the uptime page."""

from __future__ import annotations

from an_website import UPTIME
from an_website.uptime import uptime
from an_website.utils import utils


def test_calculate_uptime() -> None:
    """Test the calculation of the uptime."""
    assert UPTIME.get() < UPTIME.get()
    assert UPTIME.get() + 1 > UPTIME.get()

    assert utils.time_to_str(UPTIME.get())


def test_get_availability_dict() -> None:
    """Test the get_availability_dict function."""
    assert uptime.get_availability_dict(10, 90) == {
        "up": 10,
        "down": 90,
        "total": 100,
        "percentage": 10.0,
    }
    assert uptime.get_availability_dict(90, 10) == {
        "up": 90,
        "down": 10,
        "total": 100,
        "percentage": 90.0,
    }
    assert uptime.get_availability_dict(50, 50) == {
        "up": 50,
        "down": 50,
        "total": 100,
        "percentage": 50.0,
    }
    assert uptime.get_availability_dict(42, 0) == {
        "up": 42,
        "down": 0,
        "total": 42,
        "percentage": 100.0,
    }
    assert uptime.get_availability_dict(0, 0) == {
        "up": 0,
        "down": 0,
        "total": 0,
        "percentage": None,
    }


if __name__ == "__main__":
    test_calculate_uptime()
    test_get_availability_dict()
