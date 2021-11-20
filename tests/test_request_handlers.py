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

import pytest

from an_website import __main__ as main


@pytest.fixture
def app():
    """Create the application."""
    return main.make_app()


# pylint: disable=too-many-statements
async def test_request_handlers(http_server_client):
    """Check if the request handlers return 200 codes."""

    async def fetch(url):
        """Fetch a url."""
        return await http_server_client.fetch(url, raise_error=False)

    response = await fetch("/")
    assert response.code == 200
    response = await fetch("/redirect/?from=/&to=https://github.com")
    assert response.code == 200
    response = await fetch("/uptime/")
    assert response.code == 200
    response = await fetch("/discord/api/")
    assert response.code == 200
    response = await fetch("/version/")
    assert response.code == 200
    response = await fetch("/suche/")
    assert response.code == 200
    response = await fetch("/kaenguru-comics/")
    assert response.code == 200
    response = await fetch("/hangman-loeser/")
    assert response.code == 200
    response = await fetch("/hangman-loeser/api/")
    assert response.code == 200
    response = await fetch("/wortspiel-helfer/")
    assert response.code == 200
    response = await fetch("/wortspiel-helfer/api/")
    assert response.code == 200
    response = await fetch("/services-list/")
    assert response.code == 200
    response = await fetch("/vertauschte-woerter/")
    assert response.code == 200
    response = await fetch("/vertauschte-woerter/api/")
    assert response.code == 200
    response = await fetch("/waehrungs-rechner/")
    assert response.code == 200
    response = await fetch("/waehrungs-rechner/api/")
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
    response = await fetch("/qwertzuiop/")
    assert response.code == 404
