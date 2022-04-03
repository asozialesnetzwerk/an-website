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

from . import (
    FetchCallable,
    app,
    assert_valid_html_response,
    assert_valid_json_response,
    assert_valid_redirect,
    assert_valid_response,
    assert_valid_rss_response,
    fetch,
)

assert fetch and app


async def test_json_apis(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Check whether the APIs return valid JSON."""
    json_apis = (
        "/api/endpunkte",
        "/api/version",
        "/api/betriebszeit",
        "/api/discord",
        "/api/discord/367648314184826880",
        "/api/discord",
        "/api/ip",
        # "/api/zitate/1-1",  # gets tested with quotes
        "/api/hangman-loeser",
        # "/api/ping",  # (not JSON)
        "/api/vertauschte-woerter",
        "/api/wortspiel-helfer",
        "/api/waehrungs-rechner",
    )
    for api in json_apis:
        assert_valid_json_response(await fetch(api))


async def test_not_found_handler(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Check if the not found handler works."""
    assert_valid_html_response(await fetch("/qwertzuiop"), 404)

    assert_valid_html_response(
        assert_valid_redirect(await fetch("services/index.html"), "/services")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("servvices/index.htm"), "/services")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("services/"), "/services")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("serwizes"), "/services")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("services/"), "/services")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("services///////"), "/services")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("servces?x=y"), "/services?x=y")
    )
    assert_valid_html_response(
        assert_valid_redirect(await fetch("service?x=y"), "/services?x=y")
    )

    assert_valid_redirect(await fetch("a?x=y"), "/?x=y")


async def test_permissions(
    # pylint: disable=redefined-outer-name,unused-argument
    fetch: FetchCallable,
    http_server_port: tuple[socket.socket, int],
) -> None:
    """Test stuff with permissions."""
    for key, headers in (
        (
            "",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "s0",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "s1",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "sure",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "s2",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "sure",
            },
        ),
        (
            "s3",
            {
                "X-Permission-Backdoor": "nope",
                "X-Permission-Ratelimits": "sure",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "sure",
            },
        ),
        (
            "s4",
            {
                "X-Permission-Backdoor": "sure",
                "X-Permission-Ratelimits": "nope",
                "X-Permission-Update": "nope",
                "X-Permission-Traceback": "nope",
            },
        ),
        (
            "xyzzy",
            {
                "X-Permission-Backdoor": "sure",
                "X-Permission-Ratelimits": "sure",
                "X-Permission-Update": "sure",
                "X-Permission-Traceback": "sure",
            },
        ),
    ):
        assert_valid_response(
            await fetch("/api/ping", headers={"Authorization": key}),
            "text/plain; charset=utf-8",
            200,
            headers=headers,
        )


async def test_request_handlers2(
    # pylint: disable=redefined-outer-name
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

    localhost = f"localhost:{http_server_port[1]}"
    localhost_url = f"http://{localhost}/"
    assert_valid_redirect(
        await fetch(
            f"/redirect?url={localhost_url}",
            headers={"Host": localhost},
        ),
        localhost_url,
    )
    assert_valid_redirect(
        await fetch(
            f"/redirect?url={localhost_url}&theme=blue",
            headers={"Host": localhost},
        ),
        f"{localhost_url}?theme=blue",
    )
    assert_valid_redirect(
        await fetch(
            f"/redirect?url={localhost_url}&no_3rd_party=sure",
            headers={"Host": localhost},
        ),
        f"{localhost_url}?no_3rd_party=sure",
    )
    assert_valid_json_response(
        assert_valid_redirect(
            await fetch(
                f"/redirect?url={localhost_url}&as_json=sure",
                headers={"Host": localhost},
            ),
            f"{localhost_url}?as_json=sure",
        )
    )
    assert (
        assert_valid_response(
            await fetch("/", method="HEAD"), "text/html; charset=UTF-8"
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
        response = await fetch(f"/?no_3rd_party={_b1}")
        body = response.body.decode()
        assert_valid_html_response(response)
        response = await fetch(f"/?no_3rd_party={_b2}")
        assert_valid_html_response(response)
        assert response.body.decode().replace(_b2, _b1) == body
    assert_valid_html_response(await fetch("/?c=s"))
    response = await fetch("/redirect?from=/&to=https://example.org")
    assert_valid_html_response(response)
    assert b"https://example.org" in response.body

    assert_valid_response(await fetch("/robots.txt"), "text/plain")
    assert_valid_response(await fetch("/static/robots.txt"), "text/plain")
    assert_valid_response(
        await fetch("/favicon.ico"), "image/vnd.microsoft.icon"
    )
    assert_valid_response(
        await fetch("/static/favicon.ico"), "image/vnd.microsoft.icon"
    )

    assert_valid_html_response(await fetch("/betriebszeit"))
    assert_valid_html_response(await fetch("/discord"))
    assert_valid_html_response(await fetch("/einstellungen"))
    assert_valid_html_response(await fetch("/endpunkte"))
    assert_valid_html_response(await fetch("/hangman-loeser"))
    assert_valid_html_response(await fetch("/host-info"))
    assert_valid_html_response(await fetch("/ip"))
    assert_valid_html_response(await fetch("/js-lizenzen"))
    assert_valid_html_response(await fetch("/kaenguru-comics"))
    assert_valid_html_response(await fetch("/kontakt"))
    assert_valid_html_response(await fetch("/services"))
    assert_valid_html_response(await fetch("/soundboard"))
    assert_valid_html_response(await fetch("/soundboard/personen"))
    assert_valid_html_response(await fetch("/soundboard/suche"))
    assert_valid_html_response(await fetch("/suche"))
    assert_valid_html_response(await fetch("/version"))
    assert_valid_html_response(await fetch("/vertauschte-woerter"))
    assert_valid_html_response(await fetch("/waehrungs-rechner"))
    assert_valid_html_response(await fetch("/wiki"))
    assert_valid_html_response(await fetch("/wortspiel-helfer"))

    assert_valid_json_response(await fetch("/betriebszeit?as_json=sure"))
    assert_valid_json_response(await fetch("/discord?as_json=sure"))
    assert_valid_json_response(await fetch("/einstellungen?as_json=sure"))
    assert_valid_json_response(await fetch("/endpunkte?as_json=sure"))
    assert_valid_json_response(await fetch("/hangman-loeser?as_json=sure"))
    assert_valid_json_response(await fetch("/host-info?as_json=sure"))
    assert_valid_json_response(await fetch("/ip?as_json=sure"))
    assert_valid_json_response(await fetch("/js-lizenzen?as_json=sure"))
    assert_valid_json_response(await fetch("/kaenguru-comics?as_json=sure"))
    assert_valid_json_response(await fetch("/kontakt?as_json=sure"))
    assert_valid_json_response(await fetch("/services?as_json=sure"))
    assert_valid_json_response(await fetch("/soundboard?as_json=sure"))
    assert_valid_json_response(await fetch("/soundboard/personen?as_json=sure"))
    assert_valid_json_response(await fetch("/soundboard/suche?as_json=sure"))
    assert_valid_json_response(await fetch("/suche?as_json=sure"))
    assert_valid_json_response(await fetch("/version?as_json=sure"))
    assert_valid_json_response(await fetch("/vertauschte-woerter?as_json=sure"))
    assert_valid_json_response(await fetch("/waehrungs-rechner?as_json=sure"))
    assert_valid_json_response(await fetch("/wiki?as_json=sure"))
    assert_valid_json_response(await fetch("/wortspiel-helfer?as_json=sure"))

    assert_valid_redirect(await fetch("/chat"), "https://chat.asozial.org/")

    response = await fetch("/host-info/uwu")
    assert response.code in {200, 503}
    assert_valid_html_response(response, response.code)

    assert_valid_rss_response(await fetch("/soundboard/feed"))
    assert_valid_rss_response(await fetch("/soundboard/muk/feed"))

    assert_valid_html_response(await fetch("/soundboard/muk"))
    assert_valid_html_response(await fetch("/soundboard/qwertzuiop/feed"), 404)
    assert_valid_html_response(await fetch("/soundboard/qwertzuiop"), 404)

    assert_valid_response(
        await fetch("/api/backdoor/eval"), "application/vnd.python.pickle", 401
    )
    assert_valid_response(
        await fetch("/api/backdoor/exec"), "application/vnd.python.pickle", 401
    )

    response = assert_valid_response(
        await fetch("/api/ping"), "text/plain; charset=utf-8"
    )
    assert response.body.decode() == "🏓"

    for code in range(200, 599):
        if code not in (204, 304):
            assert_valid_html_response(await fetch(f"/{code}.html"), code)
