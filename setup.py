from __future__ import annotations

from math import pi
from pathlib import Path

from setuptools import setup  # type: ignore[import]

setup(
    name="an-website",
    license="AGPLv3+",
    version=str(pi)[:4],  # TODO
    author="Das Asoziale Netzwerk",
    author_email="contact@asozial.org",
    description="#1 Website in the Worlds",
    url="https://github.com/asozialesnetzwerk/an-website",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    packages=["an_website"],
    python_requires=">=3.10",
    install_requires=[
        spam
        for spam in Path("requirements.txt").read_text("utf-8").split("\n")
        if spam and not (spam.startswith("#") or "://" in spam)
    ],
    include_package_data=True,
    zip_safe=False,
)
