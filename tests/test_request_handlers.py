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
from urllib.parse import urlsplit

from . import (
    FetchCallable,
    app,
    assert_url_query,
    assert_valid_html_response,
    assert_valid_json_response,
    assert_valid_redirect,
    assert_valid_response,
    assert_valid_rss_response,
    assert_valid_yaml_response,
    check_html_page,
    fetch,
)

assert fetch and app


async def test_json_apis(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
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
        if not api == "/api/betriebszeit":
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


async def test_not_found_handler(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Check if the not found handler works."""
    assert_valid_html_response(await fetch("/qwertzuiop"), {404})

    await assert_valid_redirect(fetch, "/services.html", "/services", {308})
    await assert_valid_redirect(fetch, "/services/", "/services", {308})
    await assert_valid_redirect(fetch, f"/services{'/'*8}", "/services", {308})

    await assert_valid_redirect(fetch, "/serices/index.htm", "/serices", {308})
    await assert_valid_redirect(fetch, "/serices", "/services", {307})

    await assert_valid_redirect(fetch, "/serwizes", "/services", {307})
    await assert_valid_redirect(fetch, "/service?x=y", "/services?x=y", {307})
    await assert_valid_redirect(fetch, "/servces?x=y", "/services?x=y", {307})

    await assert_valid_redirect(fetch, "/a?x=y", "/?x=y", {307})

    await assert_valid_redirect(fetch, "/index.php", "/", {308})
    assert_valid_html_response(
        await fetch(
            "/index.php", method="POST", allow_nonstandard_methods=True
        ),
        {404},
    )

    assert_valid_html_response(await fetch("/wp-login.php"), {469})


async def test_page_crawling(
    # pylint: disable=redefined-outer-name,unused-argument
    fetch: FetchCallable,
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
        if urlsplit(url).path.startswith(("/static/", "/soundboard/files/")):
            assert_url_query(url, theme=None, no_3rd_party=None, dynload=None)
        else:
            assert_url_query(url, theme="pink", no_3rd_party=None, dynload=None)

    urls_3rd_party: set[str] = set()
    await check_html_page(
        fetch,
        "/?no_3rd_party=sure",
        recursive=6,
        checked_urls=urls_3rd_party,
    )
    for url in urls_3rd_party:
        if urlsplit(url).path.startswith(("/static/", "/soundboard/files/")):
            assert_url_query(url, theme=None, no_3rd_party=None, dynload=None)
        else:
            assert_url_query(url, theme=None, no_3rd_party="sure", dynload=None)

    urls_dynload: set[str] = set()
    await check_html_page(
        fetch,
        "/?dynload=sure",
        recursive=6,
        checked_urls=urls_dynload,
    )
    for url in urls_dynload:
        if urlsplit(url).path.startswith(("/static/", "/soundboard/files/")):
            assert_url_query(url, theme=None, no_3rd_party=None, dynload=None)
        else:
            assert_url_query(url, theme=None, no_3rd_party=None, dynload="sure")


async def test_request_handlers2(
    # pylint: disable=redefined-outer-name, unused-argument
    fetch: FetchCallable,
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
    ).body.decode("utf-8")
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


async def test_request_handlers(
    # pylint: disable=redefined-outer-name, too-many-statements
    fetch: FetchCallable,
) -> None:
    """Check if the request handlers return 200 codes."""
    response = await fetch("/")
    assert response.code == 200
    for theme in ("default", "blue", "random", "random-dark"):
        assert_valid_html_response(await fetch(f"/?theme={theme}"))
    for _b1, _b2 in (("sure", "true"), ("nope", "false")):
        response = await check_html_page(fetch, f"/?no_3rd_party={_b1}")
        body = response.body.decode()
        response = await check_html_page(fetch, f"/?no_3rd_party={_b2}")
        assert (
            response.body.decode().replace(
                f"no_3rd_party={_b2}", f"no_3rd_party={_b1}"
            )
            == body
        )
    assert_valid_html_response(await fetch("/?c=s"))
    response = await check_html_page(
        fetch, "/redirect?from=/&to=https://example.org"
    )
    assert b"https://example.org" in response.body

    assert_valid_response(
        await fetch("/humans.txt"), "text/plain;charset=utf-8"
    )
    assert_valid_response(
        await fetch("/static/humans.txt"), "text/plain;charset=utf-8"
    )
    assert_valid_response(
        await fetch("/robots.txt"), "text/plain;charset=utf-8"
    )
    assert_valid_response(
        await fetch("/static/robots.txt"), "text/plain;charset=utf-8"
    )
    assert_valid_response(await fetch("/favicon.png"), "image/png")
    assert_valid_response(await fetch("/static/favicon.png"), "image/png")

    await check_html_page(fetch, "/betriebszeit")
    await check_html_page(fetch, "/discord")
    await check_html_page(fetch, "/einstellungen")
    await check_html_page(fetch, "/endpunkte")
    await check_html_page(fetch, "/hangman-loeser")
    await check_html_page(fetch, "/host-info")
    await check_html_page(fetch, "/ip")
    await check_html_page(fetch, "/js-lizenzen")
    await check_html_page(fetch, "/kaenguru-comics")
    await check_html_page(fetch, "/kontakt")
    await check_html_page(fetch, "/services")
    await check_html_page(fetch, "/soundboard")
    await check_html_page(fetch, "/soundboard/personen")
    await check_html_page(fetch, "/soundboard/suche")
    await check_html_page(fetch, "/suche")
    await check_html_page(fetch, "/version")
    await check_html_page(fetch, "/vertauschte-woerter")
    await check_html_page(fetch, "/waehrungs-rechner")
    await check_html_page(fetch, "/wiki")
    await check_html_page(fetch, "/wortspiel-helfer")

    assert_valid_json_response(
        await fetch("/betriebszeit", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/discord", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/einstellungen", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/endpunkte", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/hangman-loeser", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/host-info", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/ip", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/js-lizenzen", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/kaenguru-comics", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/kontakt", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/services", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/soundboard", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch(
            "/soundboard/personen", headers={"Accept": "application/json"}
        )
    )
    assert_valid_json_response(
        await fetch("/soundboard/suche", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/suche", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/version", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch(
            "/vertauschte-woerter", headers={"Accept": "application/json"}
        )
    )
    assert_valid_json_response(
        await fetch(
            "/waehrungs-rechner", headers={"Accept": "application/json"}
        )
    )
    assert_valid_json_response(
        await fetch("/wiki", headers={"Accept": "application/json"})
    )
    assert_valid_json_response(
        await fetch("/wortspiel-helfer", headers={"Accept": "application/json"})
    )

    await assert_valid_redirect(fetch, "/chat", "https://chat.asozial.org")

    response = await fetch("/host-info/uwu")
    assert response.code in {200, 503}
    assert_valid_html_response(response, {response.code})

    assert_valid_rss_response(await fetch("/soundboard/feed"))
    assert_valid_rss_response(await fetch("/soundboard/muk/feed"))
    assert_valid_rss_response(await fetch("/soundboard/qwertzuiop/feed"), {404})

    await check_html_page(fetch, "/soundboard/muk")
    assert_valid_html_response(await fetch("/soundboard/qwertzuiop"), {404})

    assert_valid_response(
        await fetch("/api/backdoor/exec"),
        "application/vnd.python.pickle",
        {401},
    )

    response = assert_valid_response(
        await fetch("/api/ping"), "text/plain;charset=utf-8"
    )
    assert response.body.decode() == "????\n"

    for boolean in (False, True):
        url = (
            "/@elastic/apm-rum@^5/dist/bundles/elastic-apm-rum"
            f".umd{'.min' if boolean else ''}.js"
        )
        assert_valid_response(
            await fetch(url, follow_redirects=True),
            "application/javascript",
        )
    assert_valid_response(
        await fetch(url + ".map", follow_redirects=True),
        "application/json",
    )

    for code in range(200, 599):
        if code not in (204, 304):
            assert_valid_html_response(await fetch(f"/{code}.html"), {code})
