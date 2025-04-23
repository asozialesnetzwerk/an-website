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
from setuptools.build_meta import SetupRequirementsError

BACKEND_REQUIRES: set[str] = set()
DULWICH = "dulwich"
GET_VERSION = "get-version"
TROVE_CLASSIFIERS = "trove-classifiers"
TIME_MACHINE = "time-machine"
ZOPFLIPY = "zopflipy"

WHEEL_BUILD_DEPS: Set[str] = {TIME_MACHINE, ZOPFLIPY}

filterwarnings("ignore", "", UserWarning, "setuptools.dist")

EGGINFO = "egg_info" in sys.argv[1:]
SDIST = "sdist" in sys.argv[1:]

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

try:
    import zopfli
except ModuleNotFoundError:
    BACKEND_REQUIRES.add(ZOPFLIPY)
else:
    zipfile.ZipFile = zopfli.ZipFile  # type: ignore[assignment, misc]


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
        try:
            # pylint: disable=redefined-outer-name
            from get_version import get_version

            return get_version(__file__, vcs="git")
        except ModuleNotFoundError:
            BACKEND_REQUIRES.add(GET_VERSION)
    return Distribution.at(path(".")).version


def path(path: str | PathLike[str]) -> Path:
    """Return the absolute path to the file."""
    # pylint: disable=redefined-outer-name
    return Path(__file__).resolve().parent / path


if EGGINFO and path("pip-constraints.txt").exists():
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

if path(".git").exists():
    try:
        from dulwich.repo import Repo
    except ModuleNotFoundError:
        BACKEND_REQUIRES.add(DULWICH)
    else:
        repo = Repo(path(".").as_posix())
        path("REVISION.TXT").write_bytes(repo.head())
        obj = repo[repo.head()]
        dt = datetime.fromtimestamp(
            obj.author_time, timezone(timedelta(seconds=obj.author_timezone))
        )
        path("TIMESTMP.TXT").write_text(dt.isoformat(), encoding="UTF-8")
        del dt, obj, repo, Repo

    try:
        import trove_classifiers as trove
    except ModuleNotFoundError:
        BACKEND_REQUIRES.add(TROVE_CLASSIFIERS)
    else:
        assert all(_ in trove.classifiers for _ in classifiers)
        assert classifiers == sorted(classifiers)

try:
    import time_machine
except ModuleNotFoundError:
    BACKEND_REQUIRES.add(TIME_MACHINE)
else:
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

    tarfile.open = Tarfile.open  # type: ignore[assignment]


# <cursed>
compress_script_path = path("scripts/compress_static_files.py")
if compress_script_path.exists():
    compress_spec = spec_from_file_location(
        "compress_static_files", compress_script_path
    )
    assert compress_spec and compress_spec.loader
    compress_module = module_from_spec(compress_spec)
    compress_spec.loader.exec_module(compress_module)
    if EGGINFO:
        BACKEND_REQUIRES.update(compress_module.get_missing_dependencies())
    elif SDIST:
        for _ in compress_module.compress_static_files():
            pass
    del compress_spec, compress_module
del compress_script_path
# </cursed>

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
    entry_points={
        "console_scripts": (
            "an-website = an_website.__main__:main",
            "an-backdoor-client = an_website.backdoor_client:main",
        )
    },
)

if BACKEND_REQUIRES:
    raise SetupRequirementsError(
        {get_constraints()[dep] for dep in BACKEND_REQUIRES}
    )

for t, _, file in dist.dist_files:
    if t != "sdist":
        continue
    if not file.endswith(".gz"):
        continue
    f = zopfli.ZOPFLI_FORMAT_GZIP  # type: ignore[possibly-undefined]
    d = zopfli.ZopfliDecompressor(f)
    data = d.decompress(Path(file).read_bytes()) + d.flush()
    c = zopfli.ZopfliCompressor(f)
    Path(file).write_bytes(c.compress(data) + c.flush())
