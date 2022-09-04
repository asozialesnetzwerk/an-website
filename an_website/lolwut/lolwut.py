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

from typing import ClassVar

from redis.asyncio import Redis
from tornado.web import HTTPError

from .. import EVENT_REDIS
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/LOLWUT", LOLWUT),
            (r"/LOLWUT/((?:\d+/)*\d+)", LOLWUT),
            (r"/API/LOLWUT", LOLWUTAPI),
            (r"/API/LOLWUT/((?:\d+/)*\d+)", LOLWUTAPI),
        ),
        name="LOLWUT",
        description="LOLWUT; präsentiert von Redis",
        path="/LOLWUT",
        keywords=(
            "LOLWUT",
            "Redis",
        ),
    )


async def generate_art(
    redis: Redis[str],
    args: None | str = None,
    head: bool = False,
) -> None | str:
    """Generate art."""
    if args:
        arguments = args.split("/")
        for argument in arguments:
            if not argument:
                raise HTTPError(404)
        command = "LOLWUT VERSION " + " ".join(arguments)
    else:
        command = "LOLWUT"
    if head:
        return None
    return await redis.execute_command(command)  # type: ignore[no-any-return, no-untyped-call]  # noqa: B950  # pylint: disable=line-too-long, useless-suppression


class LOLWUT(HTMLRequestHandler):
    """The request handler for the LOLWUT page."""

    async def get(self, args: None | str = None, *, head: bool = False) -> None:
        """Handle GET requests to the LOLWUT page."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        art = await generate_art(self.redis, args, head)

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

    async def get(self, args: None | str = None, *, head: bool = False) -> None:
        """Handle GET requests to the LOLWUT API."""
        if not EVENT_REDIS.is_set():
            raise HTTPError(503)

        art = await generate_art(self.redis, args, head)

        if self.content_type == "text/plain":
            return await self.finish(art)

        await self.finish({"LOLWUT": art})
