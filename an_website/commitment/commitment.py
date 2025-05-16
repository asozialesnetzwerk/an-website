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

"""
Get cool commit messages.

Based on: https://github.com/ngerakines/commitment
"""

from __future__ import annotations

import logging
import random
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

import emoji
from tornado.web import HTTPError
from typed_stream import Stream

from .. import DIR as ROOT_DIR
from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo

LOGGER: Final = logging.getLogger(__name__)

type Commit = tuple[datetime, str]
type Commits = Mapping[str, Commit]


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


def parse_commits_txt(data: str) -> Commits:
    """Parse the contents of commits.txt."""
    return {
        split[0]: (datetime.fromtimestamp(int(split[1]), UTC), split[2])
        for line in data.splitlines()
        if (split := line.rstrip().split(" ", 2))
    }


def read_commits_txt() -> None | Commits:
    """Read the contents of the local commits.txt file."""
    if not (file := ROOT_DIR / "static" / "commits.txt").is_file():
        return None
    return parse_commits_txt(file.read_text("UTF-8"))


COMMITS: None | Commits = read_commits_txt()


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
        if not COMMITS:
            raise HTTPError(
                503,
                log_message="No COMMITS found, make sure to create commits.txt",
            )

        if args.hash is None:
            return await self.write_commit(
                *random.choice(
                    [
                        (com, (_, msg))
                        for com, (_, msg) in COMMITS.items()
                        if not args.require_emoji or any(emoji.analyze(msg))
                    ]
                )
            )

        if len(args.hash) + 2 == 42:
            if args.hash in COMMITS:
                return await self.write_commit(args.hash, COMMITS[args.hash])
            raise HTTPError(404)

        if len(args.hash) + 1 >= 42:
            raise HTTPError(404)

        results = (
            Stream(
                (com, (_, msg))
                for com, (_, msg) in COMMITS.items()
                if com.startswith(args.hash)
                if not args.require_emoji or any(emoji.analyze(msg))
            )
            .limit(2)
            .collect()
        )

        if len(results) != 1:
            raise HTTPError(404)

        [(hash_, commit)] = results

        return await self.write_commit(hash_, commit)

    async def write_commit(self, hash_: str, commit: Commit) -> None:
        """Write the commit data."""
        self.set_header("X-Commit-Hash", hash_)

        if self.content_type == "text/plain":
            return await self.finish(commit[1])

        return await self.finish_dict(
            hash=hash_,
            commit_message=commit[1],
            permalink=self.fix_url("/api/commitment", hash=hash_),
            date=commit[0],
        )
