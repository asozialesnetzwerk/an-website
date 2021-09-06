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

import datetime
from typing import Any, Optional, Tuple, Union

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import THEMES, ModuleInfo, bool_to_str


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/settings/?", SettingsPage),),
        name="Einstellungen",
        description="Stelle wichtige Sachen ein",
        path="/settings",
        keywords=(
            "Einstellungen",
            "Config",
            "Settings",
        ),
    )


class SettingsPage(BaseRequestHandler):
    """The request handler for the settings page."""

    def set_cookie(  # pylint: disable=too-many-arguments
        self,
        name: str,
        value: Union[str, bytes],
        domain: Optional[str] = None,
        expires: Optional[Union[float, Tuple, datetime.datetime]] = None,
        path: str = "/",
        expires_days: Optional[float] = 365,  # changed
        **kwargs: Any,
    ):
        """Override the set_cookie method to set expires days."""
        if "samesite" not in kwargs:
            # default for same site should be strict
            kwargs["samesite"] = "Strict"

        super().set_cookie(
            name,
            value,
            domain,
            expires,
            path,
            expires_days,
            **kwargs,
        )

    def get(self):
        """Handle get requests to the settings page."""
        save_in_cookie = self.get_request_var_as_bool(
            "save_in_cookie", default=False
        )

        replace_url_with = None

        if save_in_cookie:
            self.set_cookie("theme", self.get_theme())
            self.set_cookie(
                "no_3rd_party",
                bool_to_str(self.get_no_3rd_party()),
            )
            if (
                "theme" in self.request.query_arguments
                or "no_3rd_party" in self.request.query_arguments
            ):
                # remove all the information saved in the cookies from the url
                replace_url_with = (
                    f"{self.request.protocol}://{self.request.host}"
                    f"{self.request.path}?save_in_cookie=sure"
                )

        self.render(
            "pages/settings.html",
            theme_name=self.get_theme(),
            themes=THEMES,
            save_in_cookie=save_in_cookie,
            replace_url_with=replace_url_with,
        )
