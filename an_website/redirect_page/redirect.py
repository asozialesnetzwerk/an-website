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

This page is used to redirect user to third party websites.
The page will ask users if they want to leave this website.
"""

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/redirect/", RedirectPage),),
        name="Weiterleitungsseite",
        description="Seite, die User davon abhält versehentlich eine fremde "
        "Website zu besuchen.",
        path="/redirect/",
        hidden=True,
    )


class RedirectPage(BaseRequestHandler):
    """The redirect page that redirects you to another page."""

    async def get(self):
        """Handle the get request to the request page and render it."""
        redirect_url = self.get_query_argument("to", default="")

        if redirect_url in ("", "/"):
            # empty arg so redirect to main page
            # use fix_url to maybe add no_3rd_party
            return self.redirect(self.fix_url("/"))

        if not redirect_url.startswith("http"):
            # it is a local url, so just redirect
            # use fix_url to maybe add no_3rd_party
            return self.redirect(self.fix_url(redirect_url))

        # get the url the redirect comes from
        from_url = self.get_query_argument("from", default="/")

        await self.render(
            "pages/ask_for_redirect.html",
            redirect_url=redirect_url,
            from_url=from_url,
        )
