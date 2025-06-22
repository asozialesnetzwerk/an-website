#!/usr/bin/env python3
# THIS FILE IS CURSED, DO NOT LOOK AT IT!!!

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
# pylint: disable=import-outside-toplevel

"""Nobody inspects the spammish repetition."""

from __future__ import annotations

import os
import sys
import tarfile
import typing
import zipfile
from collections.abc import Callable, Mapping, Set
from datetime import datetime, timedelta, timezone
from functools import cache
from importlib.metadata import Distribution
from importlib.util import module_from_spec, spec_from_file_location
from os import PathLike
from pathlib import Path
from warnings import filterwarnings

from setuptools import setup

BACKEND_REQUIRES: set[str] = set()
DULWICH = "dulwich"
GET_VERSION = "get-version"
TROVE_CLASSIFIERS = "trove-classifiers"
TIME_MACHINE = "time-machine"
ZOPFLIPY = "zopflipy"

WHEEL_BUILD_DEPS: Set[str] = {TIME_MACHINE}

filterwarnings("ignore", "", UserWarning, "setuptools.dist")

HELP = "--help" in sys.argv[1:]
VERSION = "--version" in sys.argv[1:]
BUILDING = not HELP and {"sdist", "bdist_wheel"} & {*sys.argv[1:]}

classifiers = [
    "Development Status :: 5 - Production/Stable",
    (
        "License :: OSI Approved :: "
        "GNU Affero General Public License v3 or later (AGPLv3+)"
    ),
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: Implementation :: CPython",
    "Typing :: Typed",
]

os.environ.update(
    GIT_CONFIG_COUNT="1",
    GIT_CONFIG_KEY_0="core.abbrev",
    GIT_CONFIG_VALUE_0="10",
)


@cache
def get_constraints() -> Mapping[str, str]:
    """Get the constraints for the libraries."""
    constraints_file = path("pip-constraints.txt")
    if not constraints_file.exists():
        constraints_file = path("CNSTRNTS.TXT")

    return {
        line.split("==")[0].strip(): line.strip()
        for line in constraints_file.read_text("UTF-8").splitlines()
    }


def get_version() -> str:
    """Get the version."""
    if path(".git").exists():
        BACKEND_REQUIRES.add(GET_VERSION)
        try:
            # pylint: disable=redefined-outer-name
            from get_version import get_version

            version = get_version(__file__, vcs="git")
            path("VERSIONS.TXT").write_text(version + "\n")
        except ImportError:
            return "MissingNo."
    if path("VERSIONS.TXT").is_file():
        return path("VERSIONS.TXT").read_text("UTF-8").strip()
    return Distribution.at(path(".")).version


def path(path: str | PathLike[str]) -> Path:
    """Return the absolute path to the file."""
    # pylint: disable=redefined-outer-name
    return Path(__file__).resolve().parent / path


if path("pip-constraints.txt").exists() and (BUILDING or VERSION):
    path("CNSTRNTS.TXT").write_text(
        "\n".join(sorted(get_constraints()[dep] for dep in WHEEL_BUILD_DEPS))
        + "\n",
        encoding="UTF-8",
    )

    path("TESTDEPS.TXT").write_text(
        "\n".join(
            sorted(
                line
                for line in path("pip-dev-requirements.txt")
                .read_text("UTF-8")
                .splitlines()
                if line.startswith(
                    ("pytest", "html5lib==", "time-machine==", "zstandard==")
                )
            )
        )
        + "\n",
        encoding="UTF-8",
    )


if not path(".git").exists():
    pass
elif not (BUILDING or VERSION):
    BACKEND_REQUIRES.add(DULWICH)
    BACKEND_REQUIRES.add(TROVE_CLASSIFIERS)
else:
    from dulwich.repo import Repo

    repo = Repo(path(".").as_posix())
    path("REVISION.TXT").write_bytes(repo.head())
    head = repo[repo.head()]
    dt = datetime.fromtimestamp(
        head.commit_time, timezone(timedelta(seconds=head.commit_timezone))
    )
    path("TIMESTMP.TXT").write_text(dt.isoformat(), encoding="UTF-8")
    del dt, head, Repo
    with path("an_website/static/commits.txt").open("wb") as file:
        for entry in repo.get_walker():
            file.write(entry.commit.id)
            file.write(b" ")
            file.write(str(entry.commit.commit_time).encode("UTF-8"))
            file.write(b" ")
            file.write(entry.commit.message.split(b"\n")[0])
            file.write(b"\n")
            del entry
        file.flush()
    del repo, file

    if not VERSION:
        import trove_classifiers as trove

        assert all(_ in trove.classifiers for _ in classifiers)
        assert classifiers == sorted(classifiers)

        from zopfli import ZipFile

        zipfile.ZipFile = ZipFile  # type: ignore[assignment, misc]


BACKEND_REQUIRES.add(TIME_MACHINE)
if BUILDING:
    import time_machine

    time_machine.travel(
        path("TIMESTMP.TXT").read_text("UTF-8"), tick=False
    ).start()

    os.environ["SOURCE_DATE_EPOCH"] = str(int(datetime.now().timestamp()))

    class Tarfile(tarfile.TarFile):
        """Tarfile sub-class."""

        def add(self, *args: typing.Any, **kwargs: typing.Any) -> None:
            """Add stuff."""
            orig_filter: Callable[[tarfile.TarInfo], tarfile.TarInfo] = (
                kwargs.get("filter", lambda _: _)
            )

            def filter_(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
                tarinfo = orig_filter(tarinfo)
                tarinfo.mtime = datetime.now().timestamp()
                tarinfo.gid = 0
                tarinfo.gname = ""
                tarinfo.uid = 0
                tarinfo.uname = ""
                return tarinfo

            kwargs["filter"] = filter_
            return super().add(*args, **kwargs)

    tarfile.open = Tarfile.open


compress_script_path = path("scripts/compress_static_files.py")
if compress_script_path.exists():
    BACKEND_REQUIRES.add(ZOPFLIPY)
    compress_spec = spec_from_file_location(
        "compress_static_files", compress_script_path
    )
    assert compress_spec and compress_spec.loader
    compress_module = module_from_spec(compress_spec)
    compress_spec.loader.exec_module(compress_module)
    BACKEND_REQUIRES.update(compress_module.get_missing_dependencies())
    if BUILDING:
        for _ in compress_module.compress_static_files():
            pass
    del compress_spec, compress_module
del compress_script_path

install_requires = path("pip-requirements.txt").read_text("UTF-8").split("\n")
long_description = path("README.md").read_text("UTF-8")

dist = setup(
    author="Das Asoziale Netzwerk",
    author_email="contact@asozial.org",
    classifiers=classifiers,
    description="#1 Website in the Worlds",
    include_package_data=True,
    install_requires=install_requires,
    license="AGPL-3.0-or-later",
    long_description=long_description,
    long_description_content_type="text/markdown",
    name="an-website",
    packages=["an_website"],
    platforms="OS Independent",
    python_requires=">=3.12",
    url="https://github.com/asozialesnetzwerk/an-website",
    version=get_version(),
    zip_safe=True,
    setup_requires=[get_constraints()[dep] for dep in BACKEND_REQUIRES],
    entry_points={
        "console_scripts": (
            "an-website = an_website.__main__:main",
            "an-backdoor-client = an_website.backdoor_client:main",
        )
    },
)

for t, _, dist_file in dist.dist_files:
    if t != "sdist":
        continue
    if not dist_file.endswith(".gz"):
        continue

    import zopfli

    f = zopfli.ZOPFLI_FORMAT_GZIP
    d = zopfli.ZopfliDecompressor(f)
    data = d.decompress(Path(dist_file).read_bytes()) + d.flush()
    c = zopfli.ZopfliCompressor(f)
    Path(dist_file).write_bytes(c.compress(data) + c.flush())
