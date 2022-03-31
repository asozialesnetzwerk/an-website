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

import os
import sys
import time

import orjson
from get_version import get_version

DIR = os.path.dirname(__file__)

START_TIME = time.monotonic()

NAME = "an-website"
VERSION = get_version(__file__, vcs="git")
GIT_URL = "https://github.com/asozialesnetzwerk"
REPO_URL = f"{GIT_URL}/{NAME}"

STATIC_DIR = os.path.join(DIR, "static")
TEMPLATES_DIR = os.path.join(DIR, "templates")

ORJSON_OPTIONS = (
    orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC | orjson.OPT_UTC_Z
)

if sys.flags.dev_mode:
    NAME += "-dev"
