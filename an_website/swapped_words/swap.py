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

"""Page that swaps words."""
from __future__ import annotations

import base64
from typing import Optional

from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import GIT_URL, ModuleInfo, PageInfo
from . import DIR
from .sw_config_file import InvalidConfigException, SwappedWordsConfig


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/vertauschte-woerter/?", SwappedWords),
            (r"/swapped-words/?", SwappedWords),
            (r"/vertauschte-woerter/api", SwappedWordsApi),
            (r"/swapped-words/api", SwappedWordsApi),
        ),
        name="Vertauschte Wörter",
        description="Eine Seite, die Wörter vertauscht",
        path="/vertauschte-woerter",
        keywords=("vertauschte", "Wörter", "witzig", "Känguru"),
        sub_pages=(
            PageInfo(
                name="Plugin",
                description="Ein Browser-Plugin, welches Wörter vertauscht.",
                path=f"{GIT_URL}/VertauschteWoerterPlugin/",
            ),
        ),
    )


# the max char code of the text to process.
MAX_CHAR_COUNT: int = 32768

with open(f"{DIR}/config.sw", encoding="utf-8") as file:
    DEFAULT_CONFIG: SwappedWordsConfig = SwappedWordsConfig(file.read())


def check_text_too_long(text: str):
    """Raise an http error if the text is too long."""
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


class SwappedWords(BaseRequestHandler):
    """The request handler for the swapped words page."""

    def handle_text(self, text: str, config_str: Optional[str]):
        """Use the text to display the html page."""
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

            if config_str in (None, "DEFAULT"):
                sw_config = DEFAULT_CONFIG
            else:
                sw_config = SwappedWordsConfig(config_str)

            self.render(
                "pages/swapped_words.html",
                text=text,
                output=sw_config.swap_words(text),
                config=sw_config.to_config_str(),
                MAX_CHAR_COUNT=MAX_CHAR_COUNT,
                error_msg=None,
            )
        except InvalidConfigException as _e:
            self.render(
                "pages/swapped_words.html",
                text=text,
                output="",
                config=config_str,
                MAX_CHAR_COUNT=MAX_CHAR_COUNT,
                error_msg=str(_e),
            )

    def get(self):
        """Handle get requests to the swapped words page."""
        self.handle_text(
            self.get_query_argument("text", default=""),
            self.get_query_argument("config", default=None),
        )

    def post(self):
        """Handle post requests to the swapped words page."""
        self.handle_text(
            self.get_argument("text", default=""),
            self.get_argument("config", default=None),
        )


class SwappedWordsApi(APIRequestHandler):
    """The request handler for the swapped words api."""

    def get(self):
        """Handle get requests to the swapped words api."""
        text = self.get_argument("text", default="")
        config_str = self.get_argument("config", default=None)

        check_text_too_long(text)

        if config_str is None:
            sw_config = DEFAULT_CONFIG
        else:
            sw_config = SwappedWordsConfig(config_str)

        try:
            self.finish(
                {
                    "config": sw_config.to_config_str(minified=True),
                    "replaced_text": sw_config.swap_words(text),
                }
            )
        except InvalidConfigException as _e:
            self.finish(
                {
                    "error": _e.reason,
                    "line": _e.line,
                    "line_num": _e.line_num,
                    "config": config_str,
                }
            )
