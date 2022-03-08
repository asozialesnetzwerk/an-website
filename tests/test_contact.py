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

"""Tests for the contact page."""

from __future__ import annotations

from email.message import Message

from an_website.contact import contact


def test_add_geoip_info_to_message() -> None:
    """Test the add_geoip_info_to_message function."""
    geoip = {
        "continent_name": "Oceania",
        "country_name": "Australia",
        "location": {"lon": 143.2104, "lat": -33.494},
        "country_iso_code": "AU",
        "timezone": "Australia/Sydney",
    }

    message = Message()
    contact.add_geoip_info_to_message(message, geoip)

    # pylint: disable=protected-access
    assert message._headers == [  # type: ignore[attr-defined]
        ("X-GeoIP-continent-name", "Oceania"),
        ("X-GeoIP-country-name", "Australia"),
        ("X-GeoIP-location-lon", "143.2104"),
        ("X-GeoIP-location-lat", "-33.494"),
        ("X-GeoIP-country-iso-code", "AU"),
        ("X-GeoIP-timezone", "Australia/Sydney"),
    ]


def test_add_geoip_info_to_message_recursive() -> None:
    """Test infinite recursion."""
    geoip = {"spam": "eggs"}
    geoip["GeoIP"] = geoip  # type: ignore[assignment]
    message = Message()
    try:
        contact.add_geoip_info_to_message(message, geoip)
    except RecursionError:
        return
    raise AssertionError


if __name__ == "__main__":
    test_add_geoip_info_to_message()
    test_add_geoip_info_to_message_recursive()
