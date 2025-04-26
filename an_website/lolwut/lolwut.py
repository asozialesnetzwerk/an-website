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

"""The page that generates art."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import ClassVar, Final

import regex
from redis.asyncio import Redis
from tornado.web import HTTPError

from .. import EVENT_REDIS
from ..utils.base_request_handler import BaseRequestHandler
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    args = r"(?:\d+/)*\d+"
    return ModuleInfo(
        handlers=(
            (r"/LOLWUT", LOLWUT),
            (rf"/LOLWUT/({args})", LOLWUT),
            (r"/api/LOLWUT", LOLWUTAPI),
            (rf"/api/LOLWUT/({args})", LOLWUTAPI),
            (rf"(?i)(?:/api)?/lolwut(?:/{args})?", LOLWUTRedirectHandler),
        ),
        name="LOLWUT",
        description="LOLWUT; präsentiert von Redis",
        path="/LOLWUT",
        keywords=(
            "LOLWUT",
            "Redis",
        ),
    )


def generate_art(redis: Redis[str], args: str | None) -> Awaitable[bytes]:
    """Generate art."""
    return redis.lolwut(*(args.split("/") if args else ()))


class LOLWUT(HTMLRequestHandler):
    """The request handler for the LOLWUT page."""

    async def get(self, args: None | str = None, *, head: bool = False) -> None:
        """Handle GET requests to the LOLWUT page."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        art = await generate_art(self.redis, args)

        if head:
            return

        await self.render(
            "ansi2html.html",
            ansi=art,
            powered_by="https://redis.io",
            powered_by_name="Redis",
        )


class LOLWUTAPI(APIRequestHandler):
    """The request handler for the LOLWUT API."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "text/plain",
        *APIRequestHandler.POSSIBLE_CONTENT_TYPES,
    )

    async def get(self, args: None | str = None) -> None:
        """Handle GET requests to the LOLWUT API."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        art = await generate_art(self.redis, args)

        if self.content_type == "text/plain":
            return await self.finish(art)

        await self.finish({"LOLWUT": art})


class LOLWUTRedirectHandler(BaseRequestHandler):
    """Redirect to the LOLWUT page."""

    REPL_PATTERN: Final = regex.compile(r"/lolwut(/|\?|$)", regex.IGNORECASE)

    def get(self) -> None:
        """Handle requests to the LOLWUT page."""
        self.redirect(
            LOLWUTRedirectHandler.REPL_PATTERN.sub(
                LOLWUTRedirectHandler.repl_match, self.request.full_url(), 1
            )
        )

    head = get
    post = get

    @staticmethod
    def repl_match(match: regex.Match[str]) -> str:
        """Return the correct replacement for the given match."""
        return f"/LOLWUT{match.group(1)}"
