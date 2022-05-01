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

"""Toot cool stuff to the world."""

from __future__ import annotations

from urllib.parse import urlencode, urlsplit

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/troet", Troeter),),
        name="Tröter",
        description="Tröte witzige Sachen in die Welt",
        path="/troet",
        aliases=("/toot",),
        keywords=("Tröt", "Mastodon", "Toot"),
        hidden=True,  # TODO: remove this line
    )


class Troeter(HTMLRequestHandler):
    """The request handler that makes tooting easier."""

    def saved_mastodon_instance(self) -> None | str:
        """Get the mastodon instance saved in a cookie."""
        return self.get_cookie("mastodon-instance")

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the page."""
        text: str = self.get_argument("text", default="") or ""
        instance: None | str = self.get_argument("instance", default=None)
        save: bool = self.get_bool_argument("save", False)

        if not instance:
            instance = self.saved_mastodon_instance()

        if instance:
            if "://" not in instance:
                instance = f"https://{instance}"
            scheme, netloc = urlsplit(instance)[:2]
            if netloc:
                instance = f"{scheme}://{netloc}".rstrip("/")
                if save:
                    self.set_cookie(
                        "mastodon-instance",
                        instance,
                        path="/troet",
                        expires_days=90,
                    )
                if text:
                    self.redirect(
                        f"{instance}/share?{urlencode({'text': text})}"
                    )
                    return

        if head:
            return

        await self.render(
            "pages/troet.html",
            text=text,
            instance=instance or "",
            save=save,
        )
