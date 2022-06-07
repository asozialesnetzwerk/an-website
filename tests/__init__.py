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

"""Utilities used by the tests of an-website."""

from __future__ import annotations

import configparser
import os
import re
import socket
import sys
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any, cast

import orjson as json
import pytest
import tornado.httpclient
import tornado.web
import yaml
from blake3 import blake3  # type: ignore
from lxml import etree  # type: ignore
from lxml.html import document_fromstring  # type: ignore
from lxml.html.html5parser import HTMLParser  # type: ignore

DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(DIR)

WRONG_QUOTE_DATA = {
    # https://zitate.prapsschnalinen.de/api/wrongquotes/1
    "id": 1,
    "author": {
        "id": 2,
        "author": "Kim Jong-il",
    },
    "quote": {
        "id": 1,
        "author": {
            "id": 1,
            "author": "Abraham Lincoln",
        },
        "quote": (
            "Frage nicht, was dein Land für dich tun kann, "
            "frage, was du für dein Land tun kannst."
        ),
    },
    "rating": 4,
    "showed": 216,
    "voted": 129,
}

# add parent dir to sys.path
# this makes importing an_website possible
sys.path.append(PARENT_DIR)

from an_website import main  # noqa  # pylint: disable=wrong-import-position
from an_website import quotes  # noqa  # pylint: disable=wrong-import-position
from an_website.patches import (  # noqa  # pylint: disable=wrong-import-position
    apply,
)
from an_website.utils.utils import (  # noqa  # pylint: disable=wrong-import-position
    ModuleInfo,
)

apply()

FetchCallable = Callable[..., Awaitable[tornado.httpclient.HTTPResponse]]


@pytest.fixture
def app() -> tornado.web.Application:
    """Create the application."""
    config = configparser.ConfigParser(interpolation=None)
    config.read(os.path.join(DIR, "config.ini"))

    main.setup_logging(config, testing=True)

    for module_name in config.get(
        "GENERAL", "IGNORED_MODULES", fallback=""
    ).split(","):
        module_name = module_name.strip()  # pylint: disable=redefined-loop-name
        if len(module_name) > 0:
            main.IGNORED_MODULES.append(module_name)

    app = main.make_app()  # pylint: disable=redefined-outer-name

    assert isinstance(app, tornado.web.Application)

    app.settings["debug"] = True
    app.settings["TESTING"] = True

    main.apply_config_to_app(app, config)

    return app


def assert_url_query(url: str, /, **args: None | str) -> None:
    """Assert properties of an url."""
    query_str = urllib.parse.urlsplit(url or "/").query

    query: dict[str, str] = (
        dict(urllib.parse.parse_qsl(query_str, True, True)) if query_str else {}
    )

    for key, value in args.items():
        if value is None:
            assert key not in query
        else:
            assert key in query or print(url, key, value)
            assert query[key] == value or print(url, key, value)


@pytest.fixture
def fetch(
    http_client: tornado.httpclient.AsyncHTTPClient,
    http_server_port: tuple[socket.socket, int],
) -> FetchCallable:
    """Fetch a URL."""
    quotes.parse_wrong_quote(WRONG_QUOTE_DATA)
    host = f"http://127.0.0.1:{http_server_port[1]}"
    return lambda url, **kwargs: http_client.fetch(
        url
        if url.startswith("http://") or url.startswith("https://")
        else f"{host}/{url.removeprefix('/')}",
        **{"raise_error": False, "follow_redirects": False, **kwargs},
    )


async def assert_valid_redirect(
    _fetch: FetchCallable,
    path: str,
    new_path: str,
    codes: frozenset[int] | set[int] = frozenset({307, 308}),
    **kwargs: Any,
) -> tornado.httpclient.HTTPResponse:
    """Assert a valid redirect to a new url."""
    response = await _fetch(path, **kwargs)
    assert response.code in codes or print(response.code, path, codes)

    base_url = response.request.url.removesuffix(path)

    real_new_path = response.headers["Location"].removeprefix(base_url) or "/"
    if real_new_path.startswith("?"):
        real_new_path = f"/{real_new_path}"
    assert real_new_path == new_path or print(path, new_path, real_new_path)

    return response


def assert_valid_response(
    response: tornado.httpclient.HTTPResponse,
    content_type: None | str,
    code: int = 200,
    headers: None | dict[str, Any] = None,
) -> tornado.httpclient.HTTPResponse:
    """Assert a valid response with the given code and content type header."""
    url = response.effective_url
    assert response.code == code or print(code, url, response)

    if (
        response.headers["Content-Type"].startswith(("application/", "text/"))
        and response.headers["Content-Type"] != "application/vnd.python.pickle"
        and response.body
        and url != "https://minceraft.asozial.org/"
    ):
        assert response.body.endswith(b"\n") or print(
            f"body from {url} doesn't end with newline"
        )

    headers = headers or {}
    if content_type is not None:
        headers["Content-Type"] = content_type

    for header, value in headers.items():
        assert response.headers[header] == value or print(
            url, response.headers, header, value
        )
    return response


async def check_html_page(
    _fetch: FetchCallable,
    url: str | tornado.httpclient.HTTPResponse,
    code: int = 200,
    *,
    recursive: int = 0,
    checked_urls: set[str] = set(),  # noqa: B006
) -> tornado.httpclient.HTTPResponse:
    """Check a html page."""
    if isinstance(url, str):
        response = await _fetch(url)
    else:
        response = url
        url = response.effective_url
    assert_valid_html_response(response, code)

    html = document_fromstring(
        response.body.decode("utf-8"), base_url=response.effective_url
    )
    assert html.find("head") is not None or print("no head found", url)
    assert html.find("body") is not None or print("no body found", url)
    html.make_links_absolute(response.effective_url)
    eff_url = urllib.parse.urlsplit(response.effective_url)
    scheme_and_host = f"{eff_url.scheme}://{eff_url.netloc}"
    checked_urls.add(url.removeprefix(scheme_and_host) or "/")
    found_ref_to_body = False
    responses_to_check: list[tornado.httpclient.HTTPResponse] = []
    for link_tuple in html.iterlinks():
        assert (  # do not allow http links to other unencrypted pages
            link_tuple[2].startswith(scheme_and_host)
            or link_tuple[2].startswith(
                (
                    "https:",
                    "mailto:",
                    "whatsapp:",
                    "http://📙.la/",
                )
            )
            or urllib.parse.urlsplit(link_tuple[2]).netloc.endswith(".onion")
            or print(link_tuple[2], "is not https")
        )
        if (
            # ignore canonical urls, cuz they have no query
            link_tuple[0].tag == "link"
            and link_tuple[1] == "href"
            and link_tuple[0].attrib.get("rel") == "canonical"
            # ignore actions, cuz the stuff gets set with hidden input
            or link_tuple[1] == "action"
        ):
            continue
        if link_tuple[2] == response.effective_url + "#body":
            found_ref_to_body = True  # every page should have a skip to content
        link: str = link_tuple[2].split("#")[0]
        assert link == link.strip()
        if (
            link.startswith(scheme_and_host)
            and (link.removeprefix(scheme_and_host) or "/") not in checked_urls
        ):
            checked_urls.add(link.removeprefix(scheme_and_host) or "/")
            _response = assert_valid_response(
                await _fetch(link, follow_redirects=True),
                content_type=None,  # ignore Content-Type
            )
            if (
                _response.headers["Content-Type"] == "text/html; charset=UTF-8"
                and _response.effective_url.startswith(scheme_and_host)
                and recursive > 0
            ):
                responses_to_check.append(_response)
            if (
                link.startswith(f"{scheme_and_host}/static/")
                or link.startswith(f"{scheme_and_host}/soundboard/files/")
                and _response.headers["Content-Type"]
                != "text/html; charset=UTF-8"
            ):
                # check if static file is linked with correct hash as v
                file_hash = cast(str, blake3(_response.body).hexdigest(8))
                assert_url_query(link, v=file_hash)
    assert found_ref_to_body or print(url)
    for _r in responses_to_check:
        await check_html_page(
            _fetch,
            _r,
            recursive=recursive - 1,
            checked_urls=checked_urls,
        )
    return response


def assert_valid_html_response(
    response: tornado.httpclient.HTTPResponse,
    code: int = 200,
    effective_url: None | str = None,
) -> tornado.httpclient.HTTPResponse:
    """Assert a valid html response with the given code."""
    assert_valid_response(response, "text/html; charset=UTF-8", code)
    body = response.body.decode("utf-8")
    # check if body is valid html5
    root: etree.ElementTree = HTMLParser(
        strict=True, namespaceHTMLElements=False
    ).parse(body)
    effective_url = effective_url or response.effective_url.split("#")[0]
    # check if the canonical link is present in the doc
    assert (
        (url_in_doc := root.find("./head/link[@rel='canonical']").get("href"))
        == effective_url.split("?")[0].rstrip("/")
    ) or print(url_in_doc, effective_url)
    # check for template strings, that didn't get replaced
    matches = re.findall(r"{\s*[a-zA-Z_]+\s*}", response.body.decode("utf-8"))
    assert not matches or print(effective_url, matches)

    return response


def assert_valid_rss_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> etree.ElementTree:
    """Assert a valid html response with the given code."""
    assert_valid_response(response, "application/rss+xml; charset=UTF-8", code)
    body = response.body
    parsed_xml: etree.ElementTree = etree.fromstring(
        body,
        parser=etree.XMLParser(recover=False, resolve_entities=False),
        base_url=response.request.url,
    )
    return parsed_xml


def assert_valid_yaml_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> Any:
    """Assert a valid yaml response with the given code."""
    assert_valid_response(response, "application/yaml; charset=UTF-8", code)
    parsed = yaml.full_load(response.body)
    assert parsed is not None and len(parsed)
    return parsed


def assert_valid_json_response(
    response: tornado.httpclient.HTTPResponse, code: int = 200
) -> Any:
    """Assert a valid html response with the given code."""
    assert_valid_response(response, "application/json; charset=UTF-8", code)
    parsed_json = json.loads(response.body)
    assert parsed_json is not None and len(parsed_json)
    return parsed_json
