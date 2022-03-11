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

"""A page that swaps words."""

from __future__ import annotations

import base64
import os

from tornado.web import HTTPError

from .. import GIT_URL
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, PageInfo, str_to_bool
from . import DIR
from .sw_config_file import InvalidConfigError, SwappedWordsConfig


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/vertauschte-woerter", SwappedWords),
            (r"/api/vertauschte-woerter", SwappedWordsAPI),
        ),
        name="Vertauschte Wörter",
        description="Eine Seite, die Wörter vertauscht",
        path="/vertauschte-woerter",
        keywords=("vertauschte", "Wörter", "witzig", "Känguru"),
        sub_pages=(
            PageInfo(
                name="Plugin",
                description="Ein Browser-Plugin, welches Wörter vertauscht",
                path=f"{GIT_URL}/VertauschteWoerterPlugin",
            ),
        ),
        aliases=(
            "/swapped-words",
            "/vertauschte-wörter",
            "/vertauschte-w%C3%B6rter",
        ),
    )


# the max char count of the text to process
MAX_CHAR_COUNT: int = 32768

with open(os.path.join(DIR, "config.sw"), encoding="utf-8") as file:
    DEFAULT_CONFIG: SwappedWordsConfig = SwappedWordsConfig(file.read())


def check_text_too_long(text: str) -> None:
    """Raise an HTTP error if the text is too long."""
    len_text = len(text)

    if len_text > MAX_CHAR_COUNT:
        raise HTTPError(
            413,
            reason=(
                f"The text has {len_text} characters, but it is only allowed "
                f"to have {MAX_CHAR_COUNT} characters. That's "
                f"{len_text - MAX_CHAR_COUNT} characters too much."
            ),
        )


class SwappedWords(HTMLRequestHandler):
    """The request handler for the swapped words page."""

    def handle_text(
        self, text: str, config_str: None | str, reset: str
    ) -> None:
        """Use the text to display the HTML page."""
        check_text_too_long(text)

        try:
            if config_str is None:
                _c = self.get_cookie(
                    name="swapped-words-config",
                    default=None,
                )
                if _c is not None:
                    # decode the base64 text
                    config_str = str(
                        base64.b64decode(_c.encode("utf-8")), "utf-8"
                    )
            else:
                # save the config in a cookie
                self.set_cookie(
                    name="swapped-words-config",
                    value=str(
                        # encode the config as base64
                        base64.b64encode(config_str.encode("utf-8")),
                        "utf-8",
                    ),
                    expires_days=1000,
                    path=self.request.path,
                    SameSite="Strict",
                )

            sw_config = (
                DEFAULT_CONFIG
                if config_str is None or str_to_bool(reset)
                else SwappedWordsConfig(config_str)
            )

            self.render(
                "pages/swapped_words.html",
                text=text,
                output=sw_config.swap_words(text),
                config=sw_config.to_config_str(),
                MAX_CHAR_COUNT=MAX_CHAR_COUNT,
                error_msg=None,
            )
        except InvalidConfigError as exc:
            self.render(
                "pages/swapped_words.html",
                text=text,
                output="",
                config=config_str,
                MAX_CHAR_COUNT=MAX_CHAR_COUNT,
                error_msg=str(exc),
            )

    def get(
        self, *, head: bool = False  # pylint: disable=unused-argument
    ) -> None:
        """Handle GET requests to the swapped words page."""
        self.handle_text(
            self.get_query_argument("text", default=None) or "",
            self.get_query_argument("config", default=None),
            self.get_query_argument("reset", default=None) or "nope",
        )

    def post(self) -> None:
        """Handle POST requests to the swapped words page."""
        self.handle_text(
            self.get_argument("text") or "",
            self.get_argument("config", default=None),
            self.get_argument("reset") or "nope",
        )


class SwappedWordsAPI(APIRequestHandler):
    """The request handler for the swapped words API."""

    ALLOWED_METHODS: tuple[str, ...] = ("GET", "POST")

    async def get(
        self, *, head: bool = False  # pylint: disable=unused-argument
    ) -> None:
        """Handle GET requests to the swapped words API."""
        text = self.get_argument("text", default=None, strip=True) or ""

        check_text_too_long(text)

        config_str = self.get_argument("config", default=None, strip=True)
        return_config = str(
            self.get_argument("return_config", default="nope", strip=True)
        )
        try:
            sw_config = (
                DEFAULT_CONFIG
                if config_str is None
                else SwappedWordsConfig(config_str)
            )

            if str_to_bool(return_config, False):

                minify_config = self.get_argument(
                    "minify_config", default="sure", strip=True
                )
                return await self.finish(
                    {
                        "text": text,
                        "return_config": True,
                        "config": sw_config.to_config_str(
                            minified=str_to_bool(minify_config, True)
                        ),
                        "replaced_text": sw_config.swap_words(text),
                    }
                )
            return await self.finish(
                {
                    "text": text,
                    "return_config": False,
                    "replaced_text": sw_config.swap_words(text),
                }
            )
        except InvalidConfigError as exc:
            self.set_status(400)
            return await self.finish(
                {
                    "error": exc.reason,
                    "line": exc.line,
                    "line_num": exc.line_num,
                }
            )

    async def post(self) -> None:
        """Handle POST requests to the swapped words API."""
        return await self.get()
