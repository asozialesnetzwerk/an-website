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

"""The tests for the request handlers of an-website."""

from __future__ import annotations

import socket
from datetime import datetime
from urllib.parse import quote_from_bytes

from html5lib import HTMLParser
from time_machine import travel
from tornado.simple_httpclient import SimpleAsyncHTTPClient

from an_website.utils.options import COLOUR_SCHEMES

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_url_query,
    assert_valid_dynload_response,
    assert_valid_html_response,
    assert_valid_json_response,
    assert_valid_redirect,
    assert_valid_response,
    assert_valid_rss_response,
    assert_valid_yaml_response,
    check_html_page,
    fetch,
    hill_valley,
)
from .test_settings import parse_cookie


async def test_json_apis(fetch: FetchCallable) -> None:  # noqa: F811
    """Check whether the APIs return valid JSON."""
    json_apis = (
        "/api/betriebszeit",
        "/api/discord",
        "/api/discord/367648314184826880",
        "/api/discord",
        "/api/endpunkte",
        "/api/hangman-loeser",
        "/api/ip",
        "/api/ping",
        "/api/version",
        "/api/vertauschte-woerter",
        "/api/waehrungs-rechner",
        "/api/wortspiel-helfer",
        # "/api/zitate/1-1",  # gets tested with quotes
    )
    for api in json_apis:
        json_resp = assert_valid_json_response(
            await fetch(api, headers={"Accept": "application/json"})
        )
        yaml_resp = assert_valid_yaml_response(
            await fetch(api, headers={"Accept": "application/yaml"})
        )
        if api != "/api/betriebszeit":
            assert json_resp == yaml_resp
        assert not assert_valid_response(
            await fetch(
                api, method="HEAD", headers={"Accept": "application/json"}
            ),
            "application/json",
        ).body
        assert not assert_valid_response(
            await fetch(
                api, method="HEAD", headers={"Accept": "application/yaml"}
            ),
            "application/yaml",
        ).body


async def test_invalid_utf8(fetch: FetchCallable) -> None:  # noqa: F811
    """Check that requests with invalid utf-8 work correctly."""
    replacement = "\uFFFD"
    for umlaut in "äöüÄÖÜ":
        latin1 = quote_from_bytes(umlaut.encode("latin1"))
        await assert_valid_redirect(fetch, f"/{latin1}", "/", {307})

        assert_valid_response(
            await fetch(f"/{latin1 * 100}"), "text/html;charset=utf-8", {404}
        )

        response = assert_valid_json_response(
            await fetch(f"/api/wortspiel-helfer?word={latin1}"), {200}
        )
        assert response["word"] == replacement

        response = assert_valid_json_response(
            await fetch(f"/api/hangman-loeser?input={latin1}"),
            {200},
        )
        assert response["input"] == replacement


async def test_not_found_handler(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the NotFoundHandler works."""
    assert_valid_html_response(await fetch("/qwertzuiop"), {404})
    assert_valid_html_response(
        await fetch(
            "/https:/github.com/asozialesnetzwerk/vertauschtewoerterplugin"
        ),
        {404},
    )

    await assert_valid_redirect(fetch, "/services.html", "/services", {308})
    await assert_valid_redirect(fetch, "/services/", "/services", {308})
    await assert_valid_redirect(fetch, "/services/////////", "/services", {308})

    await assert_valid_redirect(fetch, "/serices/index.htm", "/serices", {308})
    await assert_valid_redirect(fetch, "/serices", "/services", {307})

    await assert_valid_redirect(fetch, "/serwizes", "/services", {307})
    await assert_valid_redirect(fetch, "/service?x=y", "/services?x=y", {307})
    await assert_valid_redirect(fetch, "/servces?x=y", "/services?x=y", {307})

    await assert_valid_redirect(
        fetch,
        "/vertauschtewörter",
        "/vertauschte-woerter",
        {307},
        httpclient=SimpleAsyncHTTPClient(),
    )

    await assert_valid_redirect(
        fetch,
        "/vertauschtew%C3%B6rter",
        "/vertauschte-woerter",
        {307},
        httpclient=SimpleAsyncHTTPClient(),
    )
    await assert_valid_redirect(
        fetch,
        "/vertauschte-w%F6rter",
        "/vertauschte-woerter",
        {307},
        httpclient=SimpleAsyncHTTPClient(),
    )

    await assert_valid_redirect(fetch, "/a?x=y", "/?x=y", {307})

    await assert_valid_redirect(fetch, "/index.php", "/", {307})
    assert_valid_html_response(
        await fetch(
            "/index.php", method="POST", allow_nonstandard_methods=True
        ),
        {404},
    )

    assert_valid_html_response(await fetch("/wp-login.php"), {469})


async def test_page_crawling(
    fetch: FetchCallable,  # noqa: F811
    http_server_port: tuple[socket.socket, int],
) -> None:
    """Test most of the request handlers with crawling."""
    urls: set[str] = set()
    await check_html_page(fetch, "/", recursive=6, checked_urls=urls)
    for url in urls:
        assert_url_query(url, theme=None, no_3rd_party=None, dynload=None)

    urls_theme: set[str] = set()
    await check_html_page(
        fetch,
        "/?theme=pink",
        recursive=6,
        checked_urls=urls_theme,
    )
    for url in urls_theme:
        assert_url_query(url, theme="pink", no_3rd_party=None, dynload=None)

    urls_3rd_party: set[str] = set()
    await check_html_page(
        fetch,
        "/?no_3rd_party=sure",
        recursive=6,
        checked_urls=urls_3rd_party,
    )
    for url in urls_3rd_party:
        assert_url_query(url, theme=None, no_3rd_party="sure", dynload=None)

    urls_dynload: set[str] = set()
    await check_html_page(
        fetch,
        "/?dynload=sure",
        recursive=6,
        checked_urls=urls_dynload,
    )
    for url in urls_dynload:
        assert_url_query(url, theme=None, no_3rd_party=None, dynload="sure")


async def test_request_handlers0(
    fetch: FetchCallable,  # noqa: F811
    http_server_port: tuple[socket.socket, int],
) -> None:
    """Test more request handler stuff."""
    response = await fetch("/", headers={"Host": "example.org"})
    assert response.headers["Onion-Location"] == "http://test.onion/"
    assert b"http://test.onion" in response.body
    assert_valid_html_response(response, effective_url="http://example.org")

    response = await fetch("/", headers={"Host": "test.onion"})
    assert "Onion-Location" not in response.headers
    assert_valid_html_response(response, effective_url="http://test.onion")

    assert_valid_response(
        await fetch("/", headers={"Accept": "text/spam"}), None, {406}
    )

    await assert_valid_redirect(
        fetch,
        "/redirect?to=/endpunkte?x=y",
        "/endpunkte?x=y",
    )

    await assert_valid_redirect(
        fetch,
        "/redirect?theme=blue&x=y&to=/betriebszeit",
        "/betriebszeit?theme=blue",
    )
    await assert_valid_redirect(fetch, "/redirect?to=", "/", method="HEAD")
    await assert_valid_redirect(
        fetch,
        "/redirect?to=/",
        "/",
    )
    # no "to" query param, so redirect to main page
    await assert_valid_redirect(
        fetch,
        "/redirect?theme=blue",
        "/?theme=blue",
    )
    # no redirect
    assert "https://evil.com" in assert_valid_html_response(
        await fetch(
            "/redirect?theme=blue&from=/&to=https://evil.com",
        )
    ).body.decode("UTF-8")
    await fetch(
        "/redirect?theme=blue&from=/&to=https://evil.com",
        method="HEAD",
    )

    assert (
        assert_valid_response(
            await fetch("/", method="HEAD"), "text/html;charset=utf-8"
        ).body
        == b""
    )


@travel(datetime(2000 + 1, 2, 3, 4, 5, 6, 7, hill_valley), tick=False)
async def test_request_handlers1(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return 200 codes."""
    for theme in ("default", "random", "fun", "christmas"):
        response = assert_valid_html_response(await fetch(f"/?theme={theme}"))
        assert response.code == 200
        body = response.body.decode("UTF-8")
        if theme != "default":
            assert f"theme={theme}" in body
        if not theme.startswith("random"):
            assert f"/{theme}.css" in body
        assert "🦘" in body[body.find("Mit Liebe gebacken") :]
        assert "🦘" in body

    for val in ("img", "glyf_colr0", "glyf_colr1"):
        response = await check_html_page(fetch, f"/?openmoji={val}")
        assert response.code == 200
        body = response.body.decode("UTF-8")
        assert f'"{val}"' in body  # noqa: B907
        assert "🦘" in body
        if val == "img":
            assert f"/{hex(ord('🦘'))[2:].upper()}.svg" in body

    for bool1, bool2 in (("sure", "true"), ("nope", "false")):
        response = await check_html_page(fetch, f"/?no_3rd_party={bool1}")
        assert response.code == 200
        body = response.body.decode("UTF-8")
        assert "🦘" in body
        response = await check_html_page(fetch, f"/?no_3rd_party={bool2}")
        assert response.code == 200
        assert (
            response.body.decode("UTF-8").replace(
                f"no_3rd_party={bool2}", f"no_3rd_party={bool1}"
            )
            == body
        )


@travel(datetime(2000, 1, 2, 3, 4, 5, 6, hill_valley), tick=False)
async def test_colour_scheme(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the scheme query parameter."""
    assert COLOUR_SCHEMES
    for scheme in COLOUR_SCHEMES:
        response = assert_valid_html_response(await fetch(f"/?scheme={scheme}"))
        assert response.code == 200
        body = response.body.decode("UTF-8")
        if scheme != "system":
            assert f"?scheme={scheme}" in body
        html = HTMLParser(namespaceHTMLElements=False).parse(response.body)
        assert html.find(
            f".[@data-scheme={"light" if scheme == "random" else scheme!r}]"
        ), f"{scheme} should be specified in html"


@travel(datetime.fromtimestamp(1990), tick=False)
async def test_request_handlers2(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return 200 codes."""
    response = assert_valid_html_response(await fetch("/"))
    assert response.code == 200
    for cookie_header in response.headers.get_list("Set-Cookie"):
        cookie = parse_cookie(cookie_header)
        assert len(cookie) == 1
        morsel = cookie[tuple(cookie)[0]]
        assert morsel.key == "c"
        assert morsel.value == "s"


test_request_handlers3 = travel("16-4-1")(test_request_handlers2)


async def test_request_handlers4(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return 200 codes."""
    response = await fetch("/")
    assert response.code == 200

    assert_valid_html_response(await fetch("/?c=s"))
    response = await check_html_page(
        fetch, "/redirect?from=/&to=https://example.org"
    )
    assert b"https://example.org" in response.body

    assert_valid_response(
        await fetch("/humans.txt"), "text/plain; charset=UTF-8"
    )
    assert_valid_response(
        await fetch("/static/humans.txt"), "text/plain; charset=UTF-8"
    )
    assert_valid_response(
        await fetch("/robots.txt"), "text/plain; charset=UTF-8"
    )
    assert_valid_response(
        await fetch("/static/robots.txt"), "text/plain; charset=UTF-8"
    )
    assert_valid_response(await fetch("/favicon.jxl"), "image/jxl")
    assert_valid_response(await fetch("/static/favicon.jxl"), "image/jxl")
    assert_valid_response(await fetch("/favicon.png"), "image/png")
    assert_valid_response(await fetch("/static/favicon.png"), "image/png")


async def test_request_handlers5(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return 200 codes."""
    await check_html_page(fetch, "/betriebszeit", codes={200})
    await check_html_page(fetch, "/discord?ask_before_leaving=1", codes={200})
    await check_html_page(fetch, "/einstellungen", codes={200})
    await check_html_page(fetch, "/endpunkte", codes={200})
    await check_html_page(fetch, "/hangman-loeser", codes={200})
    await check_html_page(fetch, "/host-info", codes={200})
    await check_html_page(fetch, "/ip", codes={200})
    await check_html_page(fetch, "/js-lizenzen", codes={200})
    await check_html_page(fetch, "/kaenguru-comics", codes={200})
    await check_html_page(fetch, "/kontakt", codes={200})
    await check_html_page(fetch, "/services", codes={200})
    await check_html_page(fetch, "/soundboard", codes={200})
    await check_html_page(fetch, "/soundboard/personen", codes={200})
    await check_html_page(fetch, "/soundboard/suche", codes={200})
    await check_html_page(fetch, "/suche", codes={200})
    await check_html_page(fetch, "/version", codes={200})
    await check_html_page(fetch, "/vertauschte-woerter", codes={200})
    await check_html_page(fetch, "/waehrungs-rechner", codes={200})
    await check_html_page(fetch, "/wiki?ask_before_leaving=1", codes={200})
    await check_html_page(fetch, "/wortspiel-helfer", codes={200})


async def test_request_handlers6(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return 200 codes."""
    assert_valid_dynload_response(
        await fetch(
            "/betriebszeit",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/discord?ask_before_leaving=sure",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/einstellungen",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/endpunkte",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/hangman-loeser",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/host-info",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/ip", headers={"Accept": "application/vnd.asozial.dynload+json"}
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/js-lizenzen",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/kaenguru-comics",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/kontakt",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/services",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/soundboard",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/soundboard/personen",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/soundboard/suche",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/suche", headers={"Accept": "application/vnd.asozial.dynload+json"}
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/version",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/vertauschte-woerter",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/waehrungs-rechner",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/wiki?ask_before_leaving=sure",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )
    assert_valid_dynload_response(
        await fetch(
            "/wortspiel-helfer",
            headers={"Accept": "application/vnd.asozial.dynload+json"},
        ),
        {200},
    )


async def test_request_handlers7(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return 200 codes."""
    response = await fetch("/host-info/uwu")
    assert response.code in {200, 503}
    assert_valid_html_response(response, {response.code})

    assert_valid_rss_response(await fetch("/soundboard/feed"), {200})
    assert_valid_rss_response(await fetch("/soundboard/muk/feed"), {200})
    assert_valid_rss_response(await fetch("/soundboard/qwertzuiop/feed"), {404})

    await check_html_page(fetch, "/soundboard/muk")
    assert_valid_html_response(await fetch("/soundboard/qwertzuiop"), {404})

    assert_valid_response(
        await fetch("/api/backdoor/exec", method="POST", body="42"),
        "application/vnd.uqfoundation.dill",
        {401},
    )

    response = assert_valid_response(
        await fetch("/api/ping"), "text/plain;charset=utf-8"
    )
    assert response.body.decode("UTF-8") == "🏓\n"

    for boolean in (bool(_) for _ in range(2)):
        url = f"/@apm-rum/elastic-apm-rum.umd{'.min' if boolean else ''}.js"
        assert_valid_response(
            await fetch(url, follow_redirects=True),
            "text/javascript; charset=UTF-8",
            needs_to_end_with_line_feed=False,
        )
    assert_valid_response(
        await fetch(url + ".map", follow_redirects=True),  # type: ignore[possibly-undefined]  # noqa: B950
        "text/plain; charset=UTF-8",
        needs_to_end_with_line_feed=False,
    )


async def test_error_code_pages(fetch: FetchCallable) -> None:  # noqa: F811
    """Check if the request handlers return codes."""
    for code in range(200, 599):
        if code not in (204, 304):
            assert_valid_html_response(await fetch(f"/{code}.html"), {code})
