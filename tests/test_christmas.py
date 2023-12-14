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

"""Test Christmas."""

from __future__ import annotations

import time_machine

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_html_response,
    fetch,
)


@time_machine.travel("1961-12-15")
async def test_theme_on_main_page(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the random text API."""
    response = assert_valid_html_response(
        await fetch("/200.html?theme=default"), codes={200}
    )
    assert b"christmas.css" in response.body
    assert b"default.css" not in response.body
