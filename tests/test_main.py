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

"""Tests for __main__.py in the an_website module."""

from __future__ import annotations

import configparser
import re

import an_website.__main__ as main
from an_website import patches


def test_parsing_module_infos():
    """Tests about the module infos in an_website __main__."""
    module_infos = main.get_module_infos()

    # should get more than one module_info
    assert len(module_infos) > 0

    # module_infos should be sorted already; test that:
    module_infos_list = list(module_infos)
    main.sort_module_infos(module_infos_list)
    assert module_infos == tuple(module_infos_list)

    # tests about module infos
    for module_info in module_infos:
        if module_info.path is not None:
            assert module_info.path.lower() == module_info.path
            assert module_info.path.endswith("/")

            # check if at least one handler matches the path
            handler_matches_path = False
            for handler in module_info.handlers:
                if re.fullmatch(handler[0], module_info.path):
                    handler_matches_path = True
                    break
            assert handler_matches_path

    # handlers should all be at least 3 long
    assert (
        min(
            len(handler)
            for handler in main.get_all_handlers(module_infos)
            # if issubclass(handler[1], BaseRequestHandler)
        )
        == 3
    )


def test_making_app():
    """Run the making app functions, to make sure they don't fail."""
    patches.apply()

    app = main.make_app()

    # read the example config, cuz it is always the same and should always work
    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini.example")

    main.apply_config_to_app(app, config)

    # idk why; just to assert something lol
    assert app.settings["CONFIG"] == config


if __name__ == "__main__":
    test_parsing_module_infos()
