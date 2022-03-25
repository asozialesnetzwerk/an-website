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

# pylint: disable=missing-module-docstring

from __future__ import annotations

from math import pi
from pathlib import Path
from string import ascii_letters

from setuptools import setup  # type: ignore[import]

setup(
    name="an-website",
    license="AGPLv3+",
    version=str(pi)[:4],  # TODO
    platforms=["OS Independent"],
    author="Das Asoziale Netzwerk",
    author_email="contact@asozial.org",
    description="#1 Website in the Worlds",
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
    install_requires=[
        spam
        for spam in Path("requirements.txt").read_text("utf-8").split("\n")
        if spam.startswith(tuple(ascii_letters))
    ],
    include_package_data=True,
    zip_safe=False,
)
