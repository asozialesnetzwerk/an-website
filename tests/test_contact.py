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
import sys
from email.message import Message

import orjson as json
import pytest
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
    # pylint: disable=dict-init-mutate
    geoip = {"spam": "eggs"}
    geoip["sausage"] = geoip  # type: ignore[assignment]
    message = Message()
    with pytest.raises(RecursionError):
        contact.add_geoip_info_to_message(message, geoip)


async def test_sending_email() -> None:
    """Test sending emails."""
    user = f"{random.randbytes(10).hex()}"
    subject = random.randbytes(10).hex()
    content = random.randbytes(20).hex() + "\n"
    message = Message()
    message["Subject"] = subject
    message.set_payload(content)
    await asyncio.to_thread(
        contact.send_message,
        message=message,
        from_address="Marcell D'Avis <davis@1und1.de>",
        recipients=(f"an-website <{user}@restmail.net>",),
        server="restmail.net",
        port=25,
    )

    response = await AsyncHTTPClient().fetch(
        f"https://restmail.net/mail/{user}"
    )

    for email in json.loads(response.body):
        if (  # pylint: disable=too-many-boolean-expressions
            email["subject"] == subject
            and email["text"] == content
            and email["from"][0]["name"] == "Marcell D'Avis"
            and email["from"][0]["address"] == "davis@1und1.de"
            and email["to"][0]["name"] == "an-website"
            and email["to"][0]["address"] == f"{user}@restmail.net"
        ):
            break
    else:
        import __future__  # pylint: disable=import-outside-toplevel

        assert __future__.barry_as_FLUFL.mandatory < sys.version_info  # type: ignore[attr-defined]  # noqa: B950


if __name__ == "__main__":
    test_add_geoip_info_to_message()
    test_add_geoip_info_to_message_recursive()
    asyncio.run(test_sending_email())
