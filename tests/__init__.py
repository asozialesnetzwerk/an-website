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

"""The tests module, with all the tests for the an_website module."""

from __future__ import annotations

import os
import sys
from collections.abc import Awaitable, Callable
from typing import Any

import orjson as json
import pytest
import tornado.httpclient
from lxml import etree  # type: ignore[import]
from lxml.html.html5parser import HTMLParser  # type: ignore[import]

DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(DIR)

# add parent dir to sys.path
# this makes importing an_website possible
sys.path.append(f"{PARENT_DIR}")

from an_website import main  # noqa  # pylint: disable=wrong-import-position


@pytest.fixture
def app() -> tornado.web.Application:
    """Create the application."""
    _app = main.make_app()
    _app.settings["TRUSTED_API_SECRETS"] = ("xyzzy",)  # type: ignore
    return _app  # type: ignore


@pytest.fixture
def fetch(
    http_server_client: tornado.httpclient.AsyncHTTPClient,
) -> Callable[[str], Awaitable[tornado.httpclient.HTTPResponse]]:
    """Fetch a URL."""

    async def fetch_url(url: str) -> tornado.httpclient.HTTPResponse:
        """Fetch a URL."""
        return await http_server_client.fetch(url, raise_error=False)

    return fetch_url


def assert_valid_html_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> etree.ElementTree:
    """Assert a valid html response with the given code."""
    assert response.code == code or not response.request.url
    assert response.headers["Content-Type"] == "text/html; charset=UTF-8"
    body = response.body.decode("utf-8")
    root: etree.ElementTree = HTMLParser(
        strict=True, namespaceHTMLElements=False
    ).parse(body)
    assert root.find("./head/link[@rel='canonical']").get("href").rstrip(
        "/"
    ) == response.request.url.split("?")[0].rstrip("/")
    return root


def assert_valid_rss_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> etree.ElementTree:
    """Assert a valid html response with the given code."""
    assert response.code == code or not response.request.url
    assert response.headers["Content-Type"] == "application/rss+xml"
    body = response.body
    parsed_xml: etree.ElementTree = etree.fromstring(
        body,
        parser=etree.XMLParser(recover=False, resolve_entities=False),
        base_url=response.request.url,
    )
    return parsed_xml


def assert_valid_json_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> Any:
    """Assert a valid html response with the given code."""
    assert response.code == code or not response.request.url
    assert response.headers["Content-Type"] == "application/json; charset=UTF-8"
    parsed_json = json.loads(response.body)
    assert parsed_json is not None and len(parsed_json)
    return parsed_json
