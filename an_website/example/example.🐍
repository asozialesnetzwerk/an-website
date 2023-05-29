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

"""EXAMPLE."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final

from tornado.web import MissingArgumentError

from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo

LOGGER: Final = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/beispiel", Example),
            (r"/api/beispiel", ExampleAPI),
        ),
        name="EXAMPLE",
        short_name="EXAMPLE",
        description="EXAMPLE",
        path="/beispiel",
        aliases=("/example",),
        sub_pages=(),
        keywords=(),
    )


@dataclass(slots=True)
class ExampleArguments:
    """The arguments for the example page."""

    name: str = "Welt"

    def validate(self) -> None:
        """Validate this."""
        self.name = self.name.strip()
        if not self.name:
            raise MissingArgumentError("name")


class Example(HTMLRequestHandler):
    """The request handler for the example page."""

    @parse_args(type_=ExampleArguments, validation_method="validate")
    async def get(self, *, args: ExampleArguments, head: bool = False) -> None:
        """Handle GET requests to the page."""
        self.set_header("X-Name", args.name)
        if head:
            # only after all headers have been set and the status code is clear
            return
        await self.render("pages/EXAMPLE.html", name=args.name)


class ExampleAPI(APIRequestHandler):
    """The request handler for the example API."""

    @parse_args(type_=ExampleArguments, validation_method="validate")
    async def get(self, *, args: ExampleArguments, head: bool = False) -> None:
        """Handle GET requests to the API."""
        # pylint: disable=unused-argument
        await self.finish({"text": f"Hallo, {args.name}!", "name": args.name})
