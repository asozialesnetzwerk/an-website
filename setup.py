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

"""Nobody inspects the spammish repetition."""

from __future__ import annotations

from pathlib import Path

from get_version import get_version
from setuptools import setup  # type: ignore[import]

setup(
    name="an-website",
    license="AGPLv3+",
    platforms=["OS Independent"],
    author="Das Asoziale Netzwerk",
    author_email="contact@asozial.org",
    description="#1 Website in the Worlds",
    long_description_content_type="text/markdown",
    long_description=Path("README.md").read_text("utf-8"),
    version=get_version(__file__, vcs="git", dist_name="an-website"),
    url="https://github.com/asozialesnetzwerk/an-website",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: "
        "GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    packages=["an_website"],
    python_requires=">=3.10",
    install_requires=Path("requirements.txt").read_text("utf-8").split("\n"),
    include_package_data=True,
    zip_safe=False,
)
