#!/usr/bin/env python3

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

"""This script is useful for creating commits."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from os.path import dirname, join, normpath
from typing import Final

import emoji

REPO_ROOT: Final[str] = dirname(dirname(normpath(__file__)))


def main(*args: str) -> int | str:
    """Run the commit script."""
    message = " ".join(args).strip() if args else input("Message: ")
    if not emoji.emoji_count(message):
        return f"No emoji in {message!r}"

    date = datetime.now(tz=timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )
    env: dict[str, str] = {
        "GIT_DIR": join(REPO_ROOT, ".git"),
        "GIT_AUTHOR_DATE": (date_str := date.isoformat()),
        "GIT_COMMITTER_DATE": date_str,
    }
    env.update(os.environ)
    result = subprocess.run(
        ["git", "commit", "-m", message], env=env, check=False
    )

    return result.returncode


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
