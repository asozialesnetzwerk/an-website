"""
The redirect page of the website.

This page is used to redirect user to third party websites.
The page will ask users if they want to leave this website.
"""
from __future__ import annotations

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/redirect/?", RedirectPage),),
        name="Weiterleitungsseite",
        description="Seite, die User davon abhält versehentlich eine fremde "
        "Website zu besuchen.",
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
