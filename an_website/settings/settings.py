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

"""The settings page used to change settings."""

from __future__ import annotations

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import THEMES, ModuleInfo, bool_to_str


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/einstellungen", SettingsPage),),
        name="Einstellungen",
        description="Stelle wichtige Sachen ein",
        path="/einstellungen",
        keywords=(
            "Einstellungen",
            "Config",
            "Settings",
        ),
        aliases=("/config", "/settings"),
    )


class SettingsPage(HTMLRequestHandler):
    """The request handler for the settings page."""

    def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the settings page."""
        if head:
            return
        self.render(
            "pages/settings.html",
            theme_name=self.get_theme(),
            themes=THEMES,
            no_3rd_party_default=self.get_no_3rd_party_default(),
            dynload=self.get_dynload(),
            save_in_cookie=self.get_bool_argument("save_in_cookie", True),
            replace_url_with=None,
        )

    def post(self) -> None:
        """Handle POST requests to the settings page."""
        theme: str = self.get_argument("theme", None) or "default"
        no_3rd_party: bool = self.get_bool_argument(
            "no_3rd_party", self.get_no_3rd_party_default()
        )
        dynload: bool = self.get_bool_argument("dynload", False)
        save_in_cookie: bool = self.get_bool_argument("save_in_cookie", False)

        if save_in_cookie:
            self.set_cookie("theme", theme)
            self.set_cookie("no_3rd_party", bool_to_str(no_3rd_party))
            self.set_cookie("dynload", bool_to_str(dynload))
            replace_url_with = self.fix_url(
                self.request.full_url(),
                dynload=None,
                no_3rd_party=None,
                theme=None,
                save_in_cookie=None,
            )
        else:
            replace_url_with = self.fix_url(
                self.request.full_url(),
                dynload=dynload,
                no_3rd_party=no_3rd_party,
                theme=theme,
                save_in_cookie=False,
            )
            if replace_url_with != self.request.full_url():
                self.redirect(replace_url_with)
                return

        self.render(
            "pages/settings.html",
            theme_name=theme,
            themes=THEMES,
            no_3rd_party=no_3rd_party,
            no_3rd_party_default=self.get_no_3rd_party_default(),
            dynload=dynload,
            save_in_cookie=save_in_cookie,
            replace_url_with=replace_url_with,
        )
