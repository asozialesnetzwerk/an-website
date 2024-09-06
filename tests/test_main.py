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

"""The tests for the main module of an-website."""

from __future__ import annotations

import asyncio
import pathlib
import typing
from collections.abc import Mapping

import regex
from tornado.simple_httpclient import SimpleAsyncHTTPClient
from tornado.web import Application

from an_website import main, patches
from an_website.utils.base_request_handler import BaseRequestHandler
from an_website.utils.better_config_parser import BetterConfigParser

from . import (  # noqa: F401  # pylint: disable=unused-import
    PARENT_DIR,
    FetchCallable,
    app,
    assert_valid_redirect,
    fetch,
)


async def test_parsing_module_infos(
    fetch: FetchCallable,  # noqa: F811
    app: Application,  # noqa: F811
) -> None:
    """Tests about the module infos in main."""
    # pylint: disable=too-complex
    module_infos = app.settings["MODULE_INFOS"]
    # should get more than one module_info
    assert len(module_infos) > 0

    # module_infos should be sorted already; test that
    module_infos_list = list(module_infos)
    main.sort_module_infos(module_infos_list)
    assert module_infos == tuple(module_infos_list)

    arguments: set[tuple[str, str] | tuple[str, str, str]] = set()

    # tests about module infos
    for module_info in module_infos:
        if module_info.path is None:
            continue
        assert module_info.path.isascii()
        assert module_info.path.strip() == module_info.path
        assert not module_info.path.endswith("/") or module_info.path == "/"
        assert module_info.path in {module_info.path.lower(), "/LOLWUT"}

        for alias in module_info.aliases:
            assert alias.startswith("/")
            assert not alias.endswith("/")
            if module_info.path != "/chat":
                should_path: str = (
                    module_info.aliases[alias]
                    if isinstance(module_info.aliases, Mapping)
                    else module_info.path
                )
                kwargs: dict[str, typing.Any] = (
                    {}
                    if alias.isascii()
                    else {"httpclient": SimpleAsyncHTTPClient()}
                )
                await assert_valid_redirect(fetch, alias, should_path, **kwargs)

        if module_info.path != "/api/update":
            # check if at least one handler matches the path
            handler_matches_path = False
            for handler in module_info.handlers:
                if regex.fullmatch("(?i)" + handler[0], module_info.path):
                    handler_matches_path = True
                    break
            assert handler_matches_path

        if module_info.path in {
            "/chat",  # head not supported
            "/api/update",
            "/api/upload",
        }:
            continue
        if module_info.path == "/api/zufaelliger-text":
            arguments.update(
                (
                    (module_info.path, "*/*", "text/plain"),
                    (module_info.path, "text/plain"),
                    (module_info.path, "text/html"),
                )
            )
            continue
        if module_info.path.startswith("/api/"):
            should = (
                "text/plain"
                if module_info.path in {"/api/commitment", "/api/ping"}
                else "application/json"
            )
            arguments.update(
                (
                    (module_info.path, "*/*", should),
                    (module_info.path, should),
                )
            )
            continue
        arguments.update(
            (
                (module_info.path, "*/*", "text/html"),
                (module_info.path, "text/html"),
                (module_info.path, "text/markdown"),
                (module_info.path, "text/plain"),
                (module_info.path, "application/vnd.asozial.dynload+json"),
            )
        )

    # test all arguments
    await asyncio.gather(
        *(assert_valid_response(fetch, *argument) for argument in arguments)
    )

    # handlers should all be at least 3 long
    assert (
        min(
            len(handler)
            for handler in main.get_all_handlers(module_infos)
            if issubclass(handler[1], BaseRequestHandler)
        )
        == 3
    )


async def assert_valid_response(
    _fetch: FetchCallable, path: str, accept_header: str, content_type: str = ""
) -> None:
    """Assert that the response is valid."""
    follow_redirects = path in {
        "/redirect",
        "/zitat-des-tages",
    }
    valid_response_codes = {200, 503}
    if path == "/api/reports":
        valid_response_codes.add(404)
    elif path in {"/discord", "/wiki"}:
        valid_response_codes = {307}
    head_response = await _fetch(
        path,
        headers={"Accept": accept_header},
        method="HEAD",
        raise_error=False,
        follow_redirects=follow_redirects,
    )
    assert head_response.code in valid_response_codes
    assert not head_response.body
    get_response = await _fetch(
        path,
        headers={"Accept": accept_header},
        method="GET",
        raise_error=False,
        follow_redirects=follow_redirects,
    )
    assert get_response.code == head_response.code
    if get_response.code not in {204, 307, 308}:
        assert get_response.body.endswith(b"\n")
    for header in (
        "Content-Type",
        "Onion-Location",
        "Permissions-Policy",
    ):
        assert get_response.headers[header] == head_response.headers[header]
    assert get_response.headers["Content-Type"].startswith(
        content_type or accept_header
    )


def test_making_app() -> None:
    """Run the app making functions, to make sure they don't fail."""
    patches.apply()

    # read the example config, because it is always the same and should always work
    config = BetterConfigParser.from_path(
        pathlib.Path(PARENT_DIR, "config.ini.example")
    )

    application = main.make_app(config)

    main.apply_config_to_app(application, config)  # type: ignore[arg-type]

    # idk why; just to assert something lol
    assert application.settings["CONFIG"] == config  # type: ignore[union-attr]


if __name__ == "__main__":
    # test_parsing_module_infos()
    test_making_app()
