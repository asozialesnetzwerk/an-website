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

"""Share page to share quotes on multiple services."""

from __future__ import annotations

from urllib.parse import quote

from . import QuoteReadyCheckHandler, get_wrong_quote


class ShareQuote(QuoteReadyCheckHandler):
    """Request handler for the share page."""

    async def get(
        self, quote_id: str, author_id: str, *, head: bool = False
    ) -> None:
        """Handle GET requests to the share page."""
        wrong_quote = await get_wrong_quote(int(quote_id), int(author_id))
        if head:
            return
        await self.render(
            "pages/quotes/share.html",
            text=quote(str(wrong_quote)),
            # title=quote("Witziges falsch zugeordnetes Zitat!"),
            quote_url=quote(
                self.fix_url(f"/zitate/{quote_id}-{author_id}"), safe=""
            ),
            wrong_quote=str(wrong_quote),
        )
