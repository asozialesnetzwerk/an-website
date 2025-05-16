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
# pylint: disable=wrong-import-order, wrong-import-position

"""Utilities used by the tests of an-website."""

from __future__ import annotations

import sys
from os.path import abspath, dirname

from an_website.utils.utils import str_to_bool

# add parent dir to sys.path
# this makes importing an_website possible
DIR = abspath(dirname(__file__))
PARENT_DIR = abspath(dirname(DIR))
sys.path.append(PARENT_DIR)


import warnings

warnings.filterwarnings("ignore", module="defusedxml")


from an_website import patches

patches.apply()


import asyncio
import socket
from collections.abc import Awaitable, Callable, MutableMapping, Set
from datetime import datetime, timezone
from os import environ  # pylint: disable=ungrouped-imports
from pathlib import Path
from typing import Any, Final, cast
from urllib.parse import parse_qsl, urlsplit
from zoneinfo import ZoneInfo

import orjson as json
import pytest
import regex
import time_machine as tm
import yaml
from blake3 import blake3
from lxml import etree
from lxml.html import document_fromstring
from lxml.html.html5parser import HTMLParser
from openmoji_dist import VERSION as OPENMOJI_VERSION
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPResponse
from tornado.web import Application

# pylint: disable=ungrouped-imports
from an_website import EVENT_ELASTICSEARCH, EVENT_REDIS, NAME, UPTIME, main
from an_website.quotes.utils import parse_wrong_quote
from an_website.utils import elasticsearch_setup
from an_website.utils.base_request_handler import TEXT_CONTENT_TYPES
from an_website.utils.better_config_parser import BetterConfigParser

# Same as in ../scripts/fix_static_url_path.py
ERROR_QUERY: Final[str] = "XXX-COULD-NOT-ADD-HASH-XXX"

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

FetchCallable = Callable[..., Awaitable[HTTPResponse]]

# fmt: off
hill_valley = ZoneInfo("America/Los_Angeles")
destination = environ.get("DELOREAN_DESTINATION", "1985-10-26 01:24:00")
delorean = tm.travel(datetime.fromisoformat(destination).replace(tzinfo=hill_valley))
# fmt: on


def pytest_sessionstart(*_: object) -> None:
    """Travel to the past."""
    assert not tm.escape_hatch.is_travelling()
    delorean.start()
    UPTIME.reset()


def pytest_sessionfinish(*_: object) -> None:
    """Travel back to the future."""
    assert tm.escape_hatch.is_travelling()
    delorean.stop()


@pytest.fixture
def app() -> Application:
    """Create the application."""
    assert NAME.endswith("-test")

    config = BetterConfigParser.from_path(Path(DIR, "config.ini"))

    main.ignore_modules(config)
    app = main.make_app(config)  # pylint: disable=redefined-outer-name

    assert isinstance(app, Application)

    app.settings["debug"] = True

    main.apply_config_to_app(app, config)

    es = elasticsearch_setup.setup_elasticsearch(app)
    redis = main.setup_redis(app)

    loop = asyncio.get_event_loop_policy().get_event_loop()

    if es:
        try:
            loop.run_until_complete(es.transport.perform_request("HEAD", "/"))
        except Exception:  # pylint: disable=broad-except
            EVENT_ELASTICSEARCH.clear()
        else:
            if not EVENT_ELASTICSEARCH.is_set():
                loop.run_until_complete(
                    elasticsearch_setup.setup_elasticsearch_configs(
                        es, app.settings["ELASTICSEARCH_PREFIX"]
                    )
                )
            EVENT_ELASTICSEARCH.set()

    if redis:
        try:
            loop.run_until_complete(redis.ping())
        except Exception:  # pylint: disable=broad-except
            EVENT_REDIS.clear()
        else:
            if not EVENT_REDIS.is_set():
                loop.run_until_complete(
                    redis.setex(
                        (
                            f"{app.settings.get('REDIS_PREFIX')}:quote-of-the-day:"
                            f"by-date:{datetime.now(timezone.utc).date().isoformat()}"
                        ),
                        300,
                        "1-2",
                    )
                )
            EVENT_REDIS.set()

    return app


def assert_url_query(url: str, /, **args: None | str) -> None:
    """Assert properties of a URL."""
    split_url = urlsplit(url or "/")
    query_str = split_url.query
    is_static = split_url.path.startswith(
        ("/static/", "/soundboard/files/")
    ) or split_url.path in {"/favicon.png", "/favicon.jxl", "/humans.txt"}
    query: dict[str, str] = (
        dict(parse_qsl(query_str, True, True)) if query_str else {}
    )
    for key, value in args.items():
        if value is None or (is_static and key != "v"):
            assert key not in query
        elif not split_url.path.startswith("/static/js/utils/"):
            assert key in query or print(url, key, value)
            assert query[key] == value or print(url, key, value)


@pytest.fixture
def fetch(
    http_client: AsyncHTTPClient,
    http_server_port: tuple[socket.socket, int],
) -> FetchCallable:
    """Fetch a URL."""
    parse_wrong_quote(WRONG_QUOTE_DATA)
    host = f"http://127.0.0.1:{http_server_port[1]}"

    async def _fetch(
        url: str, *, httpclient: None | AsyncHTTPClient = None, **kwargs: Any
    ) -> HTTPResponse:
        """Fetch a URL."""
        if not url.startswith(("http://", "https://")):
            url = f"{host}/{url.removeprefix('/')}"
        kwargs.setdefault("raise_error", False)
        kwargs.setdefault("follow_redirects", False)
        kwargs.setdefault("use_gzip", False)
        if not kwargs.get("headers"):
            kwargs["headers"] = {}
        kwargs["headers"].setdefault("Accept", "text/html, */*")
        try:
            return await (httpclient or http_client).fetch(url, **kwargs)
        except HTTPClientError:
            print(url, kwargs)
            raise

    return _fetch


async def assert_valid_redirect(
    fetch: FetchCallable,  # pylint: disable=redefined-outer-name
    path: str,
    new_path: str,
    codes: Set[int] = frozenset({307, 308}),
    **kwargs: Any,
) -> HTTPResponse:
    """Assert a valid redirect to a new URL."""
    response = await fetch(path, **kwargs)
    assert response.code in codes or print(path, codes, response.code)
    base_url = response.request.url.removesuffix(path)
    real_new_path = response.headers["Location"].removeprefix(base_url) or "/"
    if real_new_path.startswith("?"):
        real_new_path = f"/{real_new_path}"
    assert real_new_path == new_path or print(path, new_path, real_new_path)
    return response


def assert_valid_response(
    response: HTTPResponse,
    content_type: None | str,
    codes: Set[int] = frozenset({200, 503}),
    headers: None | MutableMapping[str, Any] = None,
    needs_to_end_with_line_feed: bool = True,
) -> HTTPResponse:
    """Assert a valid response with the given status code and Content-Type."""
    url = response.effective_url
    assert response.code in codes or print(
        url, codes, response.code, response.body
    )

    assert ERROR_QUERY.encode("UTF-8") not in response.body or print(url)

    if response.request.method == "HEAD":
        assert not response.body
    else:
        assert int(response.headers["Content-Length"]) == len(response.body)

    if (
        needs_to_end_with_line_feed
        and response.request.method != "HEAD"
        and (
            (
                content_type := cast(
                    str, response.headers.get("Content-Type", "")
                )
            )
            in TEXT_CONTENT_TYPES
            or content_type.startswith("text/")
            or content_type.endswith(("+xml", "+json"))
        )
    ):
        assert response.body.endswith(b"\n") or print(
            f"Body from {url} doesn't end with newline"
        )
    headers = headers or {}
    if content_type:
        headers["Content-Type"] = content_type
    for header, value in headers.items():
        assert response.headers[header] == value or print(
            url, response.headers, header, value
        )
    return response


async def check_html_page(
    fetch: FetchCallable,  # pylint: disable=redefined-outer-name
    url: str | HTTPResponse,
    codes: Set[int] = frozenset({200, 503}),
    *,
    recursive: int = 0,
    # pylint: disable=dangerous-default-value
    checked_urls: set[str] = set(),  # noqa: B006
) -> HTTPResponse:
    """Check a HTML page."""
    if isinstance(url, str):
        response = await fetch(url)
    else:
        response = url
        url = response.effective_url
    assert_valid_html_response(response, codes)
    html = document_fromstring(
        response.body.decode("UTF-8"), base_url=response.effective_url
    )
    assert html.find("head") is not None or print("no head found", url)
    assert html.find("body") is not None or print("no body found", url)
    html.make_links_absolute(response.effective_url)
    eff_url = urlsplit(response.effective_url)
    scheme_and_netloc = f"{eff_url.scheme}://{eff_url.netloc}"
    checked_urls.add(url.removeprefix(scheme_and_netloc) or "/")
    found_ref_to_body = False
    responses_to_check: list[HTTPResponse] = []
    for link_tuple in html.iterlinks():
        assert (  # do not allow links to insecure pages
            link_tuple[2].startswith(scheme_and_netloc)
            or link_tuple[2].startswith(
                (
                    "https:",
                    "mailto:",
                    "whatsapp:",
                    "http://📙.la/",
                )
            )
            or urlsplit(link_tuple[2]).netloc.endswith(".onion")
            or print(link_tuple[2], "is not https")
        )
        if (
            # ignore canonical URLs, because they have no query string
            link_tuple[0].tag == "link"
            and link_tuple[1] == "href"
            and link_tuple[0].attrib.get("rel") == "canonical"
            # ignore actions, because the stuff gets set with hidden input
            or link_tuple[1] == "action"
        ):
            continue
        if link_tuple[2] == response.effective_url + "#main":
            found_ref_to_body = True  # every page should have a skip to content
        link: str = link_tuple[2].split("#")[0]
        assert link == link.strip()
        if (
            link.startswith(scheme_and_netloc)
            and (link.removeprefix(scheme_and_netloc) or "/")
            not in checked_urls
        ):
            checked_urls.add(link.removeprefix(scheme_and_netloc) or "/")
            resp = await fetch(link)
            if link.removeprefix(scheme_and_netloc).split("?")[0] in {
                "/discord",
                "/wiki",
            } and not str_to_bool(
                dict(parse_qsl(urlsplit(link).query, True, True)).get(
                    "ask_before_leaving", "0"
                )
            ):
                assert resp.code == 307
                continue
            assert resp.code in {307, *codes, 503}
            resp = assert_valid_response(
                await fetch(link, follow_redirects=True),
                content_type=None,  # ignore Content-Type
                codes=codes,
            )
            if (
                resp.headers["Content-Type"] == "text/html;charset=utf-8"
                and resp.effective_url.startswith(scheme_and_netloc)
                and recursive > 0
            ):
                responses_to_check.append(resp)
            if (
                link.startswith(f"{scheme_and_netloc}/static/")
                or link.startswith(f"{scheme_and_netloc}/soundboard/files/")
                and resp.headers["Content-Type"] != "text/html;charset=utf-8"
            ):
                # check if static file is linked with correct hash
                file_hash = (
                    OPENMOJI_VERSION
                    if link.startswith(f"{scheme_and_netloc}/static/openmoji")
                    else blake3(resp.body).hexdigest(8)
                )
                assert_url_query(link, v=file_hash)
    assert found_ref_to_body or print(url)
    for resp in responses_to_check:
        await check_html_page(
            fetch,
            resp,
            recursive=recursive - 1,
            checked_urls=checked_urls,
            codes=codes,
        )
    return response


def assert_valid_html_response(
    response: HTTPResponse,
    codes: Set[int] = frozenset({200, 503}),
    effective_url: None | str = None,
    assert_canonical: bool = True,
) -> HTTPResponse:
    """Assert a valid HTML response with the given status code."""
    assert_valid_response(response, "text/html;charset=utf-8", codes)
    effective_url = effective_url or response.effective_url.split("#")[0]
    body = response.body.decode("UTF-8")
    # check if body is valid HTML5
    spam = HTMLParser(namespaceHTMLElements=False)
    try:
        root = spam.parse(body)
    except Exception:
        print(repr(body))
        raise
    assert not spam.errors or print(effective_url, spam.errors, body)
    if assert_canonical:
        # check if the canonical link is present in the document
        assert (
            (
                url_in_doc := root.find("./head/link[@rel='canonical']").get(
                    "href"
                )
            )
            == effective_url.split("?")[0].rstrip("/")
        ) or print(url_in_doc, effective_url)
    # check for template strings that didn't get replaced
    matches = regex.findall(
        r"{\s*[a-zA-Z_]+\s*}", response.body.decode("UTF-8")
    )
    assert not matches or print(effective_url, matches)
    return response


def assert_valid_rss_response(
    response: HTTPResponse,
    codes: Set[int] = frozenset({200, 503}),
) -> etree._Element:
    """Assert a valid RSS response with the given status code."""
    assert_valid_response(response, "application/rss+xml", codes)
    body = response.body
    parsed_xml = etree.fromstring(
        body,
        parser=etree.XMLParser(resolve_entities=False),
        base_url=response.request.url,
    )
    return parsed_xml


def assert_valid_yaml_response(
    response: HTTPResponse,
    codes: Set[int] = frozenset({200, 503}),
) -> Any:
    """Assert a valid YAML response with the given status code."""
    assert_valid_response(response, "application/yaml", codes)
    parsed = yaml.full_load(response.body)
    assert parsed
    return parsed


def assert_valid_json_response(
    response: HTTPResponse,
    codes: Set[int] = frozenset({200, 503}),
) -> Any:
    """Assert a valid JSON response with the given status code."""
    assert_valid_response(response, "application/json", codes)
    parsed_json = json.loads(response.body)
    assert parsed_json
    return parsed_json


def assert_valid_dynload_response(
    response: HTTPResponse,
    codes: Set[int] = frozenset({200, 503}),
) -> Any:
    """Assert a valid dynload response with the given status code."""
    assert_valid_response(
        response, "application/vnd.asozial.dynload+json", codes
    )
    parsed_json = json.loads(response.body)
    assert parsed_json
    assert response.effective_url == parsed_json["url"]
    assert parsed_json["title"]
    assert "short_title" in parsed_json
    assert parsed_json["body"]
    assert "scripts" in parsed_json
    assert "stylesheets" in parsed_json
    assert "css" in parsed_json
    return parsed_json
