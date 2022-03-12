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

"""The tests for the contact page."""

from __future__ import annotations

import asyncio
import random
from email.message import Message

import orjson as json
from tornado.httpclient import AsyncHTTPClient

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


async def test_sending_email() -> None:
    """Test sending emails."""
    user = f"an-{random.randbytes(20).hex()}"
    content = "♋️" + random.randbytes(69).hex()
    subject = "🗣️" + random.randbytes(42).hex()
    message = Message()
    message.set_payload(content, "utf-8")
    message["Subject"] = subject
    contact.send_message(
        message=message,
        from_address="tests <an-website@restmail.net>",
        recipients=[f"{user}@restmail.net"],
        server="restmail.net",
        username=None,
        password=None,
        starttls=False,
        port=25,
    )

    await asyncio.sleep(5)

    response = await AsyncHTTPClient().fetch(
        f"https://restmail.net/mail/{user}"
    )

    emails = [
        email
        for email in json.loads(response.body)
        if (
            email["subject"] == subject
            and email["text"] == content
            and email["from"][0]["name"] == "tests"
            and email["from"][0]["address"] == "an-website@restmail.net"
            and not email["to"][0]["name"]
            and email["to"][0]["address"] == f"{user}@restmail.net"
            and email["headers"]["content-type"]
            == 'text/plain; charset="utf-8"'
        )
    ]
    assert len(emails) > 0


if __name__ == "__main__":
    test_add_geoip_info_to_message()
    test_add_geoip_info_to_message_recursive()
