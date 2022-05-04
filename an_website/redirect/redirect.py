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

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo, str_to_bool


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/redirect", RedirectPage),),
        name="Weiterleitungsseite",
        description=(
            "Seite, die User davon abhält versehentlich eine fremde "
            "Website zu besuchen"
        ),
        path="/redirect",
        short_name="Weiterleitung",
        hidden=True,
    )


class RedirectPage(HTMLRequestHandler):
    """The redirect page that redirects you to another page."""

    async def get(self, *, head: bool = False) -> None:
        """Handle the GET request to the request page and render it."""
        # pylint: disable=unused-argument

        referrer = self.get_argument("referrer", None)
        redirect_url = self.get_argument("to", None)
        from_url = self.get_argument("from", None)

        if not redirect_url or redirect_url == "/":
            # empty arg so redirect to main page
            # use fix_url to maybe add no_3rd_party
            return self.redirect(self.fix_url("/", as_json=self.get_as_json()))

        if redirect_url.startswith("/"):
            # it is a local URL, so just redirect
            # use fix_url to maybe add no_3rd_party
            return self.redirect(
                self.fix_url(redirect_url, as_json=self.get_as_json())
            )

        if redirect_url.rstrip("/") == "https://chat.asozial.org":
            return self.redirect("https://chat.asozial.org")

        await self.render(
            "pages/redirect.html",
            send_referrer=str_to_bool(referrer, True),
            redirect_url=redirect_url,
            from_url=from_url,
            discord=False,
        )