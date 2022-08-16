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

import contextlib
from base64 import b64encode

from ..utils.request_handler import HTMLRequestHandler
from ..utils.utils import (
    BUMPSCOSITY_VALUES,
    THEMES,
    ModuleInfo,
    bool_to_str,
    parse_bumpscosity,
    parse_openmoji_arg,
    str_to_bool,
)


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

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the settings page."""
        if head:
            return
        await self.render(  # nosec: B106
            "pages/settings.html",
            advanced_settings=self.show_advanced_settings(),
            bumpscosity=self.get_bumpscosity(),
            bumpscosity_values=BUMPSCOSITY_VALUES,
            dynload=self.get_dynload(),
            no_3rd_party_default=self.get_no_3rd_party_default(),
            openmoji=self.get_openmoji(),
            save_in_cookie=self.get_bool_argument("save_in_cookie", True),
            show_token_input=self.get_bool_argument("auth", False),
            theme_name=self.get_theme(),
            themes=THEMES,
            token="",
        )

    async def post(self) -> None:
        """Handle POST requests to the settings page."""
        advanced_settings = self.get_bool_argument("advanced_settings", False)
        bumpscosity = parse_bumpscosity(self.get_argument("bumpscosity", ""))
        dynload: bool = self.get_bool_argument("dynload", False)
        no_3rd_party: bool = self.get_bool_argument(
            "no_3rd_party", self.get_no_3rd_party_default()
        )
        openmoji = parse_openmoji_arg(self.get_argument("openmoji", ""), False)
        theme: str = self.get_argument("theme", None) or "default"

        save_in_cookie: bool = self.get_bool_argument("save_in_cookie", False)

        token = self.get_argument("access_token", "")
        access_token: None | str = (
            b64encode(token.encode("UTF-8")).decode("ASCII") if token else None
        )

        if save_in_cookie:
            if access_token:
                self.set_cookie("access_token", access_token)
            self.set_cookie("advanced_settings", bool_to_str(advanced_settings))
            if self.get_argument("bumpscosity", ""):
                self.set_cookie("bumpscosity", str(bumpscosity))
            self.set_cookie("dynload", bool_to_str(dynload))
            self.set_cookie("no_3rd_party", bool_to_str(no_3rd_party))
            self.set_cookie("openmoji", openmoji if openmoji else "nope")
            self.set_cookie("theme", theme)

            replace_url_with = self.fix_url(
                self.request.full_url(),
                access_token=None,
                advanced_settings=None,
                bumpscosity=None,
                dynload=None,
                no_3rd_party=None,
                openmoji=None,
                save_in_cookie=None,
                theme=None,
            )
        else:
            replace_url_with = self.fix_url(
                self.request.full_url(),
                access_token=access_token,
                advanced_settings=advanced_settings,
                bumpscosity=bumpscosity,
                dynload=dynload,
                no_3rd_party=no_3rd_party,
                openmoji=openmoji,
                save_in_cookie=False,
                theme=theme,
            )

        if replace_url_with != self.request.full_url():
            return self.redirect(replace_url_with)

        await self.render(
            "pages/settings.html",
            advanced_settings=self.show_advanced_settings(),
            bumpscosity=bumpscosity,
            bumpscosity_values=BUMPSCOSITY_VALUES,
            dynload=dynload,
            no_3rd_party=no_3rd_party,
            no_3rd_party_default=self.get_no_3rd_party_default(),
            openmoji=openmoji,
            save_in_cookie=save_in_cookie,
            show_token_input=token or self.get_bool_argument("auth", False),
            themes=THEMES,
            theme_name=theme,
            token=token,
        )

    def show_advanced_settings(self) -> bool:
        """Whether advanced settings should be shown."""
        if arg := self.get_argument("advanced_settings", ""):
            with contextlib.suppress(ValueError):
                return str_to_bool(arg)
        return str_to_bool(self.get_cookie("advanced_settings", ""), False)
