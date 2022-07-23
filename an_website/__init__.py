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

import orjson
from get_version import get_version

try:
    from pytest_is_running import is_running as pytest_is_running
except ImportError:

    def pytest_is_running() -> bool:  # noqa: D103
        # pylint: disable=missing-function-docstring
        return "pytest" in sys.modules


DIR = os.path.dirname(__file__)

START_TIME = time.monotonic()

EPOCH = 1651075200
EPOCH_MS = EPOCH * 1000

NAME = "an-website"
VERSION = get_version(__file__, vcs="git")
GH_ORG_URL = "https://github.com/asozialesnetzwerk"
GH_REPO_URL = f"{GH_ORG_URL}/{NAME}"
GH_PAGES_URL = f"https://github.asozial.org/{NAME}"

STATIC_DIR = os.path.join(DIR, "static")
TEMPLATES_DIR = os.path.join(DIR, "templates")

ORJSON_OPTIONS = (
    orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC | orjson.OPT_UTC_Z
)

CONTAINERIZED = "container" in os.environ or os.path.exists("/.dockerenv")

if pytest_is_running():
    NAME += "-test"
elif sys.flags.dev_mode:
    NAME += "-dev"

EVENT_SHUTDOWN = multiprocessing.Event()

EVENT_ELASTICSEARCH = Event()
EVENT_REDIS = Event()

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
    "NAME",
    "ORJSON_OPTIONS",
    "START_TIME",
    "STATIC_DIR",
    "TEMPLATES_DIR",
    "VERSION",
    "pytest_is_running",
)
