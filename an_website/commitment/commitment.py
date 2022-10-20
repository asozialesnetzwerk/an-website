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

"""Get cool commit messages.

Based on: https://github.com/ngerakines/commitment
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Final

import emoji
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo

LOGGER: Final = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/commitment", CommitmentAPI),),
        name="Commitment",
        short_name="Commitment",
        description="Zeige gute Commit-Nachrichten an.",
        path="/api/commitment",
        aliases=(),
        sub_pages=(),
        keywords=(),
        hidden=True,
    )


Commit = tuple[datetime, str]
Commits = dict[str, Commit]
COMMIT_DATA: dict[str, Commits] = {}


async def get_commit_data(committers_uri: str) -> Commits:
    """Get data from URI."""
    if committers_uri in COMMIT_DATA:
        return COMMIT_DATA[committers_uri]
    file_content: bytes
    if committers_uri.startswith(("https://", "http://")):
        file_content = (await AsyncHTTPClient().fetch(committers_uri)).body
    else:
        if committers_uri.startswith("file:///"):
            committers_uri = committers_uri.removeprefix("file://")
        with open(committers_uri, "rb") as file:
            file_content = file.read()

    data: Commits = {}

    for line in file_content.decode("UTF-8").split("\n"):
        if not line:
            continue
        hash_, date, msg = line.split(" ", 2)
        data[hash_] = (datetime.utcfromtimestamp(int(date)), msg)

    COMMIT_DATA[committers_uri] = data
    return data


@dataclass(slots=True)
class Arguments:
    """The arguments for the commitment API."""

    hash: str | None = None
    require_emoji: bool = False


class CommitmentAPI(APIRequestHandler):
    """The request handler for the commitment API."""

    POSSIBLE_CONTENT_TYPES = (
        "text/plain",
        *APIRequestHandler.POSSIBLE_CONTENT_TYPES,
    )

    @parse_args(type_=Arguments)
    async def get(self, *, args: Arguments, head: bool = False) -> None:
        """Handle GET requests to the API."""
        # pylint: disable=unused-argument
        try:
            data = await get_commit_data(self.settings["COMMITTERS_URI"])
        except Exception as exc:
            raise HTTPError(503) from exc

        if args.hash is None:
            return await self.write_commit(
                *random.choice(
                    [
                        (com, (_, msg))
                        for com, (_, msg) in data.items()
                        if not args.require_emoji or emoji.emoji_count(msg)
                    ]
                )
            )

        if len(args.hash) + 2 == 42:
            if args.hash in data:
                return await self.write_commit(args.hash, data[args.hash])
            raise HTTPError(404)

        if len(args.hash) + 1 >= 42:
            raise HTTPError(404)

        results = [
            item
            for item in data.items()
            if item[0].startswith(args.hash)
            if not args.require_emoji or emoji.emoji_count(item[1][1])
        ]

        if not results:
            raise HTTPError(404)

        results.sort(key=lambda m: m[1][0])

        return await self.write_commit(*results[0])

    async def write_commit(self, hash_: str, commit: Commit) -> None:
        """Write the commit data."""
        self.set_header("X-Message-Hash", hash_)

        if self.content_type == "text/plain":
            return await self.finish(commit[1])

        return await self.finish_dict(
            hash=hash_,
            commit_message=commit[1],
            permalink=self.fix_url("/api/commitment", hash=hash_),
            date=commit[0],
        )
