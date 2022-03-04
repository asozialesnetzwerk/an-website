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

"""Tests for main.py in the an_website package."""

from __future__ import annotations

import asyncio
import configparser
import re

from an_website import main, patches
from an_website.utils.request_handler import BaseRequestHandler
from an_website.utils.utils import ModuleInfo


async def get_module_infos() -> tuple[ModuleInfo, ...]:
    """Wrap main.get_module_infos in an async function."""
    return main.get_module_infos()


def test_parsing_module_infos() -> None:
    """Tests about the module infos in main."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    module_infos = loop.run_until_complete(get_module_infos())
    loop.close()

    # should get more than one module_info
    assert len(module_infos) > 0

    # module_infos should be sorted already; test that:
    module_infos_list = list(module_infos)
    main.sort_module_infos(module_infos_list)
    assert module_infos == tuple(module_infos_list)

    # tests about module infos
    for module_info in module_infos:
        if module_info.path is not None:
            assert not module_info.path.endswith("/") or module_info.path == "/"

            for alias in module_info.aliases:
                assert alias.startswith("/")
                assert not alias.endswith("/")

            # check if at least one handler matches the path
            handler_matches_path = False
            for handler in module_info.handlers:
                if re.fullmatch("(?i)" + handler[0], module_info.path):
                    handler_matches_path = True
                    break

            assert handler_matches_path

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

    app = main.make_app()

    # read the example config, because it is always the same and should always work
    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini.example")

    main.apply_config_to_app(app, config)

    # idk why; just to assert something lol
    assert app.settings["CONFIG"] == config


if __name__ == "__main__":
    test_parsing_module_infos()
