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


async def test_request_handlers(http_server_client):
    """Check if the request handlers return 200 codes."""
    response = await http_server_client.fetch("/")
    assert response.code == 200
    response = await http_server_client.fetch("/uptime/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-comics/")
    assert response.code == 200
    response = await http_server_client.fetch("/hangman-loeser/")
    assert response.code == 200
    response = await http_server_client.fetch("/hangman-loeser/api/")
    assert response.code == 200
    response = await http_server_client.fetch("/wortspiel-helfer/")
    assert response.code == 200
    response = await http_server_client.fetch("/wortspiel-helfer/api/")
    assert response.code == 200
    response = await http_server_client.fetch("/services-list/")
    assert response.code == 200
    response = await http_server_client.fetch("/vertauschte-woerter/")
    assert response.code == 200
    response = await http_server_client.fetch("/vertauschte-woerter/api/")
    assert response.code == 200
    response = await http_server_client.fetch("/waehrungs-rechner/")
    assert response.code == 200
    response = await http_server_client.fetch("/waehrungs-rechner/api/")
    assert response.code == 200
    response = await http_server_client.fetch("/host-info/")
    assert response.code == 200
    response = await http_server_client.fetch("/settings/")
    assert response.code == 200
    response = await http_server_client.fetch("/wiki/")
    assert response.code == 200
    response = await http_server_client.fetch("/js-lizenzen/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-soundboard/personen/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-soundboard/suche/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-soundboard/feed/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-soundboard/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-soundboard/muk/feed/")
    assert response.code == 200
    response = await http_server_client.fetch("/kaenguru-soundboard/muk/")
    assert response.code == 200
    response = await http_server_client.fetch(
        "/qwertzuiop/", raise_error=False
    )
    assert response.code == 404
