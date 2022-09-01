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

import os
import warnings
from pathlib import Path

from get_version import get_version
from setuptools import setup

warnings.filterwarnings("ignore", "", UserWarning, "setuptools.dist")


def read(filename: str) -> str:
    """Load the contents of a file."""
    root_dir = os.path.dirname(__file__)
    filepath = os.path.join(root_dir, filename)
    return Path(filepath).read_text("UTF-8")


setup(
    name="an-website",
    license="AGPLv3+",
    platforms=["OS Independent"],
    author="Das Asoziale Netzwerk",
    author_email="contact@asozial.org",
    description="#1 Website in the Worlds",
    long_description_content_type="text/markdown",
    long_description=read("README.md"),
    version=get_version(__file__, vcs="git", dist_name="an-website"),
    url="https://github.com/asozialesnetzwerk/an-website",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        (
            "License :: OSI Approved :: "
            "GNU Affero General Public License v3 or later (AGPLv3+)"
        ),
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Typing :: Typed",
    ],
    packages=["an_website"],
    python_requires=">=3.10",
    install_requires=read("requirements.txt").split("\n"),
    extras_require={"jxl": ["jxlpy~=0.9"]},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "an-website = an_website.__main__:main",
            "an-backdoor-client = an_website.backdoor.client:main",
        ]
    },
)
