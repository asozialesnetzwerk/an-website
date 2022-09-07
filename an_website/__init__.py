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
from pathlib import Path
from typing import Final, TypedDict

import orjson as json
from get_version import get_version

try:
    from pytest_is_running import is_running as pytest_is_running
except ImportError:

    def pytest_is_running() -> bool:  # noqa: D103
        # pylint: disable=missing-function-docstring
        return "pytest" in sys.modules


class MediaType(TypedDict, total=False):
    # pylint: disable=missing-class-docstring
    charset: str
    compressible: bool
    extensions: list[str]
    source: str


DIR: Final = os.path.dirname(__file__)

START_TIME_NS: Final[int] = time.monotonic_ns()

MEDIA_TYPES: dict[str, MediaType] = json.loads(
    Path(os.path.join(DIR, "media_types.json")).read_bytes()
)

EPOCH: Final[int] = 1651075200
EPOCH_MS: Final[int] = EPOCH * 1000

NAME = "an-website"
VERSION: Final[str] = get_version(__file__, vcs="git")
GH_ORG_URL: Final[str] = "https://github.com/asozialesnetzwerk"
GH_REPO_URL: Final[str] = f"{GH_ORG_URL}/{NAME}"
GH_PAGES_URL: Final[str] = f"https://github.asozial.org/{NAME}"

STATIC_DIR: Final = os.path.join(DIR, "static")
TEMPLATES_DIR: Final = os.path.join(DIR, "templates")

ORJSON_OPTIONS = json.OPT_SERIALIZE_NUMPY | json.OPT_NAIVE_UTC | json.OPT_UTC_Z

CONTAINERIZED: Final[bool] = "container" in os.environ or os.path.exists(
    "/.dockerenv"
)

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
    "START_TIME_NS",
    "STATIC_DIR",
    "TEMPLATES_DIR",
    "VERSION",
    "pytest_is_running",
)

__version__ = VERSION
