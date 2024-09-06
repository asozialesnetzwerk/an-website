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

"""The website of the AN."""

from __future__ import annotations

import multiprocessing
import os
import sys
import time
from asyncio import Event
from collections.abc import Mapping
from importlib.metadata import Distribution
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Final, TypedDict

try:
    import orjson as json

    if "spam" not in json.loads('{"spam":"eggs"}'):
        from marshal import dumps, loads

        _loads = json.loads
        json.loads = lambda *args, **kwargs: loads(  # nosec: B302
            dumps(_loads(*args, **kwargs))
        )
except ModuleNotFoundError:
    from . import fake_orjson as json  # type: ignore[no-redef]  # noqa: F811

    sys.modules["orjson"] = json

try:
    from pytest_is_running import is_running as pytest_is_running
except ModuleNotFoundError:

    def pytest_is_running() -> bool:  # noqa: D103
        # pylint: disable=missing-function-docstring
        return "pytest" in sys.modules


class MediaType(TypedDict, total=False):
    # pylint: disable=missing-class-docstring
    charset: str
    compressible: bool
    extensions: list[str]
    source: str


class UptimeTimer:
    """UptimeTimer class used for timing the uptime."""

    __slots__ = ("_start_time",)

    def __init__(self) -> None:
        self.reset()

    def get(self) -> float:
        """Get the time since start in seconds."""
        return self.get_ns() / 1_000_000_000

    def get_ns(self) -> int:
        """Get the time since start in nanoseconds."""
        return time.monotonic_ns() - self._start_time

    def reset(self) -> None:
        """Reset the timer."""
        self._start_time = time.monotonic_ns()


UPTIME: Final = UptimeTimer()

EPOCH: Final[int] = 1651075200
EPOCH_MS: Final[int] = EPOCH * 1000

DIR: Final[Traversable] = files(__name__)

MEDIA_TYPES: Final[Mapping[str, MediaType]] = json.loads(
    (DIR / "vendored" / "mime-db.json").read_bytes()
)

NAME = "an-website"


def get_version() -> str:
    """Get the version of the package."""
    if isinstance(DIR, Path):
        # pylint: disable-next=import-outside-toplevel
        from get_version import get_version as gv

        return gv(__file__, vcs="git")

    return Distribution.from_name(NAME).version


VERSION: Final[str] = get_version()

GH_ORG_URL: Final[str] = "https://github.com/asozialesnetzwerk"
GH_REPO_URL: Final[str] = f"{GH_ORG_URL}/{NAME}"
GH_PAGES_URL: Final[str] = f"https://github.asozial.org/{NAME}"

CACHE_DIR: Final[Path] = Path("~/.cache/", NAME).expanduser().absolute()
STATIC_DIR: Final[Traversable] = DIR / "static"
TEMPLATES_DIR: Final[Traversable] = DIR / "templates"

ORJSON_OPTIONS: Final[int] = (
    json.OPT_SERIALIZE_NUMPY | json.OPT_NAIVE_UTC | json.OPT_UTC_Z
)

CONTAINERIZED: Final[bool] = "container" in os.environ or os.path.exists(
    "/.dockerenv"
)


def traversable_to_file(traversable: Traversable) -> Path:
    """Convert a traversable to a path to a file directly in the fs."""
    if isinstance(traversable, Path):
        return traversable
    folder = CACHE_DIR / "temp"
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / traversable.name
    file.write_bytes(traversable.read_bytes())
    return file


CA_BUNDLE_PATH: Final[str] = traversable_to_file(
    DIR / "ca-bundle.crt"
).as_posix()


if pytest_is_running():
    NAME += "-test"
elif sys.flags.dev_mode:
    NAME += "-dev"

EVENT_SHUTDOWN: Final = multiprocessing.Event()

EVENT_ELASTICSEARCH: Final = Event()
EVENT_REDIS: Final = Event()

__all__ = (
    "CONTAINERIZED",
    "DIR",
    "EPOCH",
    "EPOCH_MS",
    "EVENT_ELASTICSEARCH",
    "EVENT_REDIS",
    "EVENT_SHUTDOWN",
    "GH_ORG_URL",
    "GH_PAGES_URL",
    "GH_REPO_URL",
    "MEDIA_TYPES",
    "NAME",
    "ORJSON_OPTIONS",
    "STATIC_DIR",
    "TEMPLATES_DIR",
    "UPTIME",
    "VERSION",
    "pytest_is_running",
)

__version__ = VERSION
