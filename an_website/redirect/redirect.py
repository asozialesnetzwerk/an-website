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

"""
The redirect page of the website.

This page is used to redirect users to third party websites.
This page will ask users if they want to leave this website.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from .. import pytest_is_running
from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/redirect", RedirectPage),),
        name="Weiterleitungsseite",
        description=(
            "Seite, die User davon abhält versehentlich eine fremde "
            "Webseite zu besuchen"
        ),
        path="/redirect",
        short_name="Weiterleitung",
        hidden=True,
    )


class RedirectPage(HTMLRequestHandler):
    """The redirect page that redirects you to another page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the redirect page."""
        # pylint: disable=unused-argument

        redirect_url = self.get_argument("to", None) or "/"
        referrer = self.request.headers.get_list("Referer")
        from_url = referrer[0] if referrer else None

        if redirect_url.startswith("/"):
            # it is a local URL, so just redirect
            # use fix_url to maybe add no_3rd_party
            return self.redirect(self.fix_url(redirect_url))

        if (
            (domain := urlsplit(redirect_url).hostname)
            and domain.endswith(".asozial.org")
            and not pytest_is_running()
        ):
            return self.redirect(redirect_url)

        await self.render(
            "pages/redirect.html",
            redirect_url=redirect_url,
            send_referrer=False,
            from_url=from_url,
            discord=False,
        )
