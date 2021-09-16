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

import an_website.__main__ as main


def test_parsing_module_infos():
    """Tests about the module infos in an_website __main__."""
    module_infos = main.get_module_infos()

    # should get more than one module_info
    assert len(module_infos) > 0

    # module_infos should be sorted already; test that:
    module_infos_list = list(module_infos)
    main.sort_module_infos(module_infos_list)
    assert module_infos == tuple(module_infos_list)

    # handlers should all be at least 3 long
    assert (
        min(len(handler) for handler in main.get_all_handlers(module_infos))
        == 3
    )


if __name__ == "__main__":
    test_parsing_module_infos()
