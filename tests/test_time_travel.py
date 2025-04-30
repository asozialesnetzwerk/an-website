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

"""Testing travelling through time."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from lxml.html import document_fromstring
from time_machine import travel

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_html_response,
    fetch,
)


async def test_time_travel(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the footer and stuff."""
    epoch = datetime(2026, 1, 1, 6, 6, 6, 6, tzinfo=UTC)

    for i in range(1000):
        now = epoch + timedelta(hours=12 * i)
        with travel(now, tick=False):
            response = assert_valid_html_response(
                await fetch("/einstellungen"), {200}
            )

        doc = document_fromstring(response.body)

        footer = doc.find("*/footer")
        assert footer is not None
        assert "Mit Liebe gebacken" in footer.text_content()
        assert " GitHub" in footer.text_content()

        assert footer is not None, f"{response.body!r}"

        emoji = next(iter(footer))

        assert emoji.tag in {"a", "span"}
        assert emoji.text_content()
        assert "Mit Liebe gebacken" not in emoji.text_content()
        assert "Sektion GitHub" not in emoji.text_content()
