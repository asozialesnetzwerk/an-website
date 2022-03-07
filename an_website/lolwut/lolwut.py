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

from aioredis import Redis
from tornado.web import HTTPError

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/LOLWUT", LOLWUT),
            (r"/LOLWUT/([0-9/]+)", LOLWUT),
            (r"/API/LOLWUT", LOLWUTAPI),
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
) -> str:
    """Generate art."""
    if not redis:
        raise HTTPError(503)
    if args:
        arguments = args.split("/")
        if not len(arguments) == 1 and not arguments[-1]:
            arguments = arguments[:-1]
        for argument in arguments:
            if not argument:
                raise HTTPError(404)
        command = "LOLWUT VERSION " + " ".join(arguments)
    else:
        command = "LOLWUT"
    # pylint: disable=line-too-long
    return await redis.execute_command(command)  # type: ignore[no-untyped-call, no-any-return]  # noqa: B950


class LOLWUT(HTMLRequestHandler):
    """The request handler for the LOLWUT page."""

    async def get(self, args: None | str = None) -> None:
        """Handle GET requests to the LOLWUT page."""
        await self.render(
            "pages/ansi2html.html",
            ansi=await generate_art(self.redis, args),
            powered_by="https://redis.io",
            powered_by_name="Redis",
        )


class LOLWUTAPI(APIRequestHandler):
    """The request handler for the LOLWUT API."""

    async def get(self, args: None | str = None) -> None:
        """Handle GET requests to the LOLWUT API."""
        self.set_header("Content-Type", "text/plain; charset=utf-8")
        await self.finish(await generate_art(self.redis, args))
