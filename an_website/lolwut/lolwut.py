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

from redis.asyncio import Redis  # type: ignore
from tornado.web import HTTPError

from ..utils.request_handler import (
    APIRequestHandler,
    HTMLRequestHandler,
    NotFoundHandler,
)
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/LOLWUT", LOLWUT),
            (r"/LOLWUT/([0-9/]+)/", NotFoundHandler),
            (r"/LOLWUT/([0-9/]+)", LOLWUT),
            (r"/API/LOLWUT", LOLWUTAPI),
            (r"/API/LOLWUT/([0-9/]+)/", NotFoundHandler),
            (r"/API/LOLWUT/([0-9/]+)", LOLWUTAPI),
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
    redis: None | Redis,
    args: None | str = None,
    head: bool = False,
) -> None | str:
    """Generate art."""
    if not redis:
        raise HTTPError(503)
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
    return await redis.execute_command(command)  # type: ignore[no-any-return]


class LOLWUT(HTMLRequestHandler):
    """The request handler for the LOLWUT page."""

    async def get(self, args: None | str = None, *, head: bool = False) -> None:
        """Handle GET requests to the LOLWUT page."""
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

    async def get(self, args: None | str = None, *, head: bool = False) -> None:
        """Handle GET requests to the LOLWUT API."""
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        await self.finish(await generate_art(self.redis, args, head))
