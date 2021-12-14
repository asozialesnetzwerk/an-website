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

"""Test the request handlers of an_website."""


from __future__ import annotations

import importlib

import orjson as json
import pytest


@pytest.fixture
def app():
    """Create the application."""
    return importlib.import_module("an_website.__main__").make_app()


@pytest.fixture
def fetch(http_server_client):
    """Fetch a URL."""

    async def fetch_url(url):
        """Fetch a URL."""
        return await http_server_client.fetch(url, raise_error=False)

    return fetch_url


async def test_json_apis(fetch):
    """Check whether the APIs return valid JSON."""
    json_apis = (
        "/api/endpoints/",
        "/api/uptime/",
        "/api/discord/",
        # "/api/discord/367648314184826880/",  # needs network access
        # "/api/discord/",  # needs network access
        # "/api/zitate/1-1/",  # gets tested with quotes
        "/api/hangman-loeser/",
        # "/api/ping/",  # (not JSON)
        # "/api/restart/",  # (not 200)
        "/api/vertauschte-woerter/",
        "/api/wortspiel-helfer/",
        "/api/waehrungs-rechner/",
    )
    for api in json_apis:
        response = await fetch(api)
        assert response.code == 200
        assert response.headers["Content-Type"] == (
            "application/json; charset=UTF-8"
        )
        print(api)
        assert json.loads(response.body.decode("utf-8"))


# pylint: disable=too-many-statements
async def test_request_handlers(fetch):
    """Check if the request handlers return 200 codes."""
    response = await fetch("/")
    assert response.code == 200
    for theme in ("default", "blue", "random", "random-dark"):
        response = await fetch(f"/?theme={theme}")
        assert response.code == 200
    for _b1, _b2 in (("sure", "true"), ("nope", "false")):
        response = await fetch(f"/?no_3rd_party={_b1}")
        body = response.body.decode()
        assert response.code == 200
        response = await fetch(f"/?no_3rd_party={_b2}")
        assert response.code == 200
        assert response.body.decode().replace(_b2, _b1) == body

    response = await fetch("/redirect/?from=/&to=https://example.org")
    assert response.code == 200
    assert b"https://example.org" in response.body
    response = await fetch("/uptime/")
    assert response.code == 200
    response = await fetch("/api/discord/")
    assert response.code == 200
    response = await fetch("/version/")
    assert response.code == 200
    response = await fetch("/api/version/")
    assert response.code == 200
    response = await fetch("/suche/")
    assert response.code == 200
    response = await fetch("/kaenguru-comics/")
    assert response.code == 200
    response = await fetch("/hangman-loeser/")
    assert response.code == 200
    response = await fetch("/api/hangman-loeser/")
    assert response.code == 200
    response = await fetch("/wortspiel-helfer/")
    assert response.code == 200
    response = await fetch("/api/wortspiel-helfer/")
    assert response.code == 200
    response = await fetch("/services-list/")
    assert response.code == 200
    response = await fetch("/vertauschte-woerter/")
    assert response.code == 200
    response = await fetch("/api/vertauschte-woerter/")
    assert response.code == 200
    response = await fetch("/waehrungs-rechner/")
    assert response.code == 200
    response = await fetch("/api/waehrungs-rechner/")
    assert response.code == 200
    response = await fetch("/host-info/")
    assert response.code == 200
    response = await fetch("/host-info/uwu/")
    assert response.code in (200, 501)
    response = await fetch("/settings/")
    assert response.code == 200
    response = await fetch("/wiki/")
    assert response.code == 200
    response = await fetch("/js-lizenzen/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/personen/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/suche/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/feed/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/muk/feed/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/muk/")
    assert response.code == 200
    response = await fetch("/kaenguru-soundboard/qwertzuiop/feed/")
    assert response.code == 404
    response = await fetch("/kaenguru-soundboard/qwertzuiop/")
    assert response.code == 404
    response = await fetch("/api/restart/")
    assert response.code == 401  # Unauthorized
    response = await fetch("/api/backdoor/eval/")
    assert response.code == 401  # Unauthorized
    response = await fetch("/api/backdoor/exec/")
    assert response.code == 401  # Unauthorized
    response = await fetch("/api/endpoints/")
    assert response.code == 200
    response = await fetch("/api/ping/")
    assert response.code == 200
    assert response.body.decode() == "🏓"
    for code in range(200, 599):
        if code not in (204, 304):
            response = await fetch(f"/{code}.html")
            assert response.code == code
    response = await fetch("/qwertzuiop/")
    assert response.code == 404
