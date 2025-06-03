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

"""The module containing the impl of the fix_static_path function."""

import logging
import os
from collections.abc import Callable, Iterable, Mapping
from importlib.resources.abc import Traversable
from pathlib import Path
from types import MappingProxyType
from typing import Final

from blake3 import blake3
from openmoji_dist import VERSION as OPENMOJI_VERSION

if "STATIC_DIR" not in locals():
    from .. import STATIC_DIR

LOGGER: Final = logging.getLogger(__name__)


def recurse_directory(
    root: Traversable,
    # pylint: disable-next=redefined-builtin
    filter: Callable[[Traversable], bool] = lambda _: True,
) -> Iterable[str]:
    """Recursively iterate over entries in a directory."""
    dirs: list[str] = ["."]
    while dirs:  # pylint: disable=while-used
        curr_dir = dirs.pop()
        for path in (root if curr_dir == "." else root / curr_dir).iterdir():
            current: str = (
                path.name
                if curr_dir == "."
                else os.path.join(curr_dir, path.name)
            )
            if path.is_dir():
                dirs.append(current)
            if filter(path):
                yield current


def hash_file(path: Traversable) -> str:
    """Hash a file with BLAKE3."""
    hasher = blake3()
    with path.open("rb") as file:
        for data in file:
            hasher.update(data)
    return hasher.hexdigest(8)


def create_file_hashes_dict(
    filter_path_fun: Callable[[str], bool] | None = None
) -> Mapping[str, str]:
    """Create a dict of file hashes."""
    static = Path("/static")
    file_hashes_dict = {
        f"{(static / path).as_posix()}": hash_file(STATIC_DIR / path)
        for path in recurse_directory(STATIC_DIR, lambda path: path.is_file())
        if not path.endswith((".map", ".gz", ".zst"))
        if filter_path_fun is None or filter_path_fun(path)
    }
    if filter_path_fun is None:
        file_hashes_dict["/favicon.png"] = file_hashes_dict[
            "/static/favicon.png"
        ]
        file_hashes_dict["/favicon.jxl"] = file_hashes_dict[
            "/static/favicon.jxl"
        ]
        file_hashes_dict["/humans.txt"] = file_hashes_dict["/static/humans.txt"]
    return MappingProxyType(file_hashes_dict)


def fix_static_path_impl(path: str, file_hashes_dict: Mapping[str, str]) -> str:
    """Fix the path for static files."""
    if not path.startswith("/"):
        path = f"/static/{path}"
    if "?" in path:
        path = path.split("?")[0]
    if path.startswith("/static/openmoji/"):
        return f"{path}?v={OPENMOJI_VERSION}"
    path = path.lower()
    if path in file_hashes_dict:
        hash_ = file_hashes_dict[path]
        return f"{path}?v={hash_}"
    LOGGER.warning("%s not in FILE_HASHES_DICT", path)
    return path
