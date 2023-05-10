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
            bumpscosity_values=BUMPSCOSITY_VALUES,
            no_3rd_party_default=self.user_settings.as_dict(
                include_argument=False, include_cookie=False
            )["no_3rd_party"],
            save_in_cookie=self.get_bool_argument("save_in_cookie", True),
            show_token_input=self.get_bool_argument("auth", False),
            themes=THEMES,
            token="",
        )

    async def post(self) -> None:
        """Handle POST requests to the settings page."""
        advanced_settings = self.get_bool_argument("advanced_settings", False)
        save_in_cookie: bool = self.get_bool_argument("save_in_cookie", False)
        token = self.get_argument("access_token", "")
        access_token: None | str = (
            b64encode(token.encode("UTF-8")).decode("ASCII") if token else None
        )

        if save_in_cookie:
            if access_token:
                self.set_cookie("access_token", access_token)
            self.set_cookie("advanced_settings", bool_to_str(advanced_settings))
            for option in self.user_settings.iter_options():
                self.set_cookie(
                    option.name, option.value_to_string(option.get_value(self))
                )

            replace_url_with = self.fix_url(
                self.request.full_url(),
                access_token=None,
                advanced_settings=None,
                save_in_cookie=None,
                **{key: None for key in self.user_settings.iter_option_names()},
            )
        else:
            replace_url_with = self.fix_url(
                self.request.full_url(),
                access_token=access_token,
                advanced_settings=advanced_settings,
                save_in_cookie=False,
                **self.user_settings.as_dict_with_str_values(),
            )

        if replace_url_with != self.request.full_url():
            return self.redirect(replace_url_with)

        await self.render(
            "pages/settings.html",
            advanced_settings=self.show_advanced_settings(),
            bumpscosity_values=BUMPSCOSITY_VALUES,
            no_3rd_party_default=self.user_settings.as_dict(
                include_argument=False, include_cookie=False
            )["no_3rd_party"],
            save_in_cookie=save_in_cookie,
            show_token_input=token or self.get_bool_argument("auth", False),
            themes=THEMES,
            token=token,
        )

    def show_advanced_settings(self) -> bool:
        """Whether advanced settings should be shown."""
        if arg := self.get_argument("advanced_settings", ""):
            with contextlib.suppress(ValueError):
                return str_to_bool(arg)
        return str_to_bool(self.get_cookie("advanced_settings", ""), False)
