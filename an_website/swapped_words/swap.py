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

import os
from asyncio import Future
from base64 import b64decode, b64encode
from dataclasses import dataclass

from tornado.web import HTTPError

from .. import GH_ORG_URL
from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo, PageInfo
from . import DIR
from .config_file import InvalidConfigError, SwappedWordsConfig


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
                path=f"{GH_ORG_URL}/VertauschteWoerterPlugin",
            ),
        ),
        aliases=(
            "/swapped-words",
            "/vertauschte-wörter",
            "/vertauschte-w%C3%B6rter",
        ),
    )


# the max char count of the text to process
MAX_CHAR_COUNT = 32768

with open(os.path.join(DIR, "config.sw"), encoding="UTF-8") as file:
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


@dataclass
class SwArgs:
    """Arguments used for swapped words."""

    text: str = ""
    config: None | str = None
    reset: bool = False
    return_config: bool = False
    minify_config: bool = False


class SwappedWords(HTMLRequestHandler):
    """The request handler for the swapped words page."""

    @parse_args(type_=SwArgs, name="data")
    async def get(self, *, head: bool = False, data: SwArgs) -> None:
        """Handle GET requests to the swapped words page."""
        # pylint: disable=unused-argument
        await self.handle_text(data)

    def handle_text(self, args: SwArgs) -> Future[None]:
        """Use the text to display the HTML page."""
        check_text_too_long(args.text)

        if args.config is None:
            cookie = self.get_cookie(
                "swapped-words-config",
                None,
            )
            if cookie is not None:
                # decode the base64 text
                args.config = b64decode(cookie).decode("UTF-8")
        else:
            # save the config in a cookie
            self.set_cookie(
                name="swapped-words-config",
                # encode the config as base64
                value=b64encode(args.config.encode("UTF-8")).decode("UTF-8"),
                expires_days=1000,
                path=self.request.path,
                SameSite="Strict",
            )

        try:
            sw_config = (
                DEFAULT_CONFIG
                if args.config is None or args.reset
                else SwappedWordsConfig(args.config)
            )
        except InvalidConfigError as exc:
            self.set_status(400)
            return self.render(
                "pages/swapped_words.html",
                text=args.text,
                output="",
                config=args.config,
                MAX_CHAR_COUNT=MAX_CHAR_COUNT,
                error_msg=str(exc),
            )
        else:  # everything went well
            return self.render(
                "pages/swapped_words.html",
                text=args.text,
                output=sw_config.swap_words(args.text),
                config=sw_config.to_config_str(),
                MAX_CHAR_COUNT=MAX_CHAR_COUNT,
                error_msg=None,
            )

    @parse_args(type_=SwArgs, name="data")
    async def post(self, *, data: SwArgs) -> None:
        """Handle POST requests to the swapped words page."""
        self.get_argument("text")  # 400 if text is missing
        await self.handle_text(data)


class SwappedWordsAPI(APIRequestHandler):
    """The request handler for the swapped words API."""

    ALLOWED_METHODS: tuple[str, ...] = ("GET", "POST")

    @parse_args(type_=SwArgs, name="args")
    async def get(self, *, head: bool = False, args: SwArgs) -> None:
        """Handle GET requests to the swapped words API."""
        # pylint: disable=unused-argument
        check_text_too_long(args.text)
        try:
            sw_config = (
                DEFAULT_CONFIG
                if args.config is None
                else SwappedWordsConfig(args.config)
            )

            if args.return_config:
                return await self.finish_dict(
                    text=args.text,
                    return_config=True,
                    minify_config=args.minify_config,
                    config=sw_config.to_config_str(args.minify_config),
                    replaced_text=sw_config.swap_words(args.text),
                )
            return await self.finish_dict(
                text=args.text,
                return_config=False,
                replaced_text=sw_config.swap_words(args.text),
            )
        except InvalidConfigError as exc:
            self.set_status(400)
            return await self.finish_dict(
                error=exc.reason,
                line=exc.line,
                line_num=exc.line_num,
            )

    async def post(self) -> None:
        """Handle POST requests to the swapped words API."""
        return await self.get()  # pylint: disable=missing-kwoa
