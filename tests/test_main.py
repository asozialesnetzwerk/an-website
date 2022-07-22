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

import configparser
import os
import re

from tornado.web import Application

from an_website import main, patches
from an_website.utils.base_request_handler import BaseRequestHandler
from an_website.utils.utils import ModuleInfo

from . import PARENT_DIR, FetchCallable, app, assert_valid_redirect, fetch

assert fetch and app


async def test_parsing_module_infos(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
    app: Application,
) -> None:
    """Tests about the module infos in main."""
    module_infos = app.settings["MODULE_INFOS"]
    # should get more than one module_info
    assert len(module_infos) > 0

    # pylint: disable=import-outside-toplevel
    from an_website.lolwut.lolwut import get_module_info as gmi1
    from an_website.quotes.quote_of_the_day import get_module_info as gmi2
    from an_website.reporting.reporting import get_module_info as gmi3

    # test excluded module infos
    assert all(isinstance(_mi, ModuleInfo) for _mi in (gmi1(), gmi2(), gmi3()))

    # module_infos should be sorted already; test that
    module_infos_list = list(module_infos)
    main.sort_module_infos(module_infos_list)
    assert module_infos == tuple(module_infos_list)

    # tests about module infos
    for module_info in module_infos:
        if module_info.path is not None:
            assert module_info.path.isascii()
            assert module_info.path.strip() == module_info.path
            assert not module_info.path.endswith("/") or module_info.path == "/"
            assert module_info.path in {module_info.path.lower(), "/LOLWUT"}

            for alias in module_info.aliases:
                assert alias.startswith("/")
                assert not alias.endswith("/")
                if module_info.path != "/chat" and alias.isascii():
                    await assert_valid_redirect(fetch, alias, module_info.path)

            if module_info.path != "/api/update":
                # check if at least one handler matches the path
                handler_matches_path = False
                for handler in module_info.handlers:
                    if re.fullmatch("(?i)" + handler[0], module_info.path):
                        handler_matches_path = True
                        break
                assert handler_matches_path

            if module_info.path not in {
                "/chat",  # head not supported
                "/api/update",
            }:
                print(module_info.path)
                head_response = await fetch(
                    module_info.path,
                    method="HEAD",
                    raise_error=False,
                    follow_redirects=module_info.path == "/redirect",
                )
                assert head_response.code != 500
                assert head_response.body == b""
                get_response = await fetch(
                    module_info.path,
                    method="GET",
                    raise_error=False,
                    follow_redirects=module_info.path == "/redirect",
                )
                assert get_response.code != 500
                assert get_response.body != b""
                for header in (
                    "Content-Type",
                    "Onion-Location",
                    "Permissions-Policy",
                ):
                    assert (
                        get_response.headers[header]
                        == head_response.headers[header]
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


def test_making_app() -> None:
    """Run the app making functions, to make sure they don't fail."""
    patches.apply()
    application = main.make_app()

    # read the example config, because it is always the same and should always work
    config = configparser.ConfigParser(interpolation=None)
    config.read(os.path.join(PARENT_DIR, "config.ini.example"))

    main.apply_config_to_app(application, config)  # type: ignore[arg-type]

    # idk why; just to assert something lol
    assert application.settings["CONFIG"] == config  # type: ignore[union-attr]


if __name__ == "__main__":
    # test_parsing_module_infos()
    test_making_app()
