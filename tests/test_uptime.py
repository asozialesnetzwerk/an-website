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

"""Test the uptime module."""
from __future__ import annotations

from an_website.uptime import uptime


def test_get_up_perc_dict() -> None:
    """Test the get_up_perc_dict function."""
    assert uptime.get_up_perc_dict(10, 90) == {
        "up": 10,
        "down": 90,
        "total": 100,
        "perc": 10.0,
    }
    assert uptime.get_up_perc_dict(90, 10) == {
        "up": 90,
        "down": 10,
        "total": 100,
        "perc": 90.0,
    }
    assert uptime.get_up_perc_dict(50, 50) == {
        "up": 50,
        "down": 50,
        "total": 100,
        "perc": 50.0,
    }
    assert uptime.get_up_perc_dict(42, 0) == {
        "up": 42,
        "down": 0,
        "total": 42,
        "perc": 100.0,
    }
    assert uptime.get_up_perc_dict(0, 0) == {
        "up": 0,
        "down": 0,
        "total": 0,
        "perc": 0.0,
    }


def test_uptime_to_str() -> None:
    """Test the uptime_to_str function."""
    assert uptime.uptime_to_str(0) == "0d 0h 0min 0s"
    assert uptime.uptime_to_str(133769420) == "1548d 6h 10min 20s"
    assert uptime.uptime_to_str(69420) == "0d 19h 17min 0s"
    assert uptime.uptime_to_str(24 * 60 * 60 + 69) == "1d 0h 1min 9s"


if __name__ == "__main__":
    test_get_up_perc_dict()
    test_uptime_to_str()