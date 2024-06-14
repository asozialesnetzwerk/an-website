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

"""This script compresses static files in a folder in place."""

from __future__ import annotations

import abc
import gzip
import shutil
import subprocess  # nosec: B404
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import ClassVar, override

type CompressionResult = tuple[Path, float, bool]


class FileCompressor(abc.ABC):
    """Compress files."""

    def compress(self, path: Path) -> CompressionResult | None:
        """Compress the file and return an error."""
        out_file = self.compressed_file(path)
        data = path.read_bytes()
        with out_file.open("wb") as file:
            for chunk in self.compress_bytes(data):
                file.write(chunk)
        compressed_size = out_file.stat().st_size
        compression_factor = compressed_size / len(data)
        if compressed_size >= len(data):
            out_file.unlink()
            return path, compression_factor, False
        return out_file, compression_factor, True

    @abc.abstractmethod
    def compress_bytes(self, data: bytes) -> Iterable[bytes]:
        """Compress bytes."""
        raise NotImplementedError()

    def compressed_file(self, path: Path) -> Path:
        """Return the path to the compressed file."""
        return path.with_suffix(f"{path.suffix}.{self.file_extension()}")

    @classmethod
    @abc.abstractmethod
    def file_extension(cls) -> str:
        """Return the file extension of the compressed files.

        e.g.: 'gz'
        """
        raise NotImplementedError()


class GzipFileCompressor(FileCompressor):
    """Compress files using gzip compression."""

    USE_PIGZ: ClassVar[bool] = True

    @override
    def compress_bytes(self, data: bytes) -> Iterable[bytes]:
        """Compress bytes."""
        if self.USE_PIGZ:
            compressed = GzipFileCompressor.compress_using_pigz(data)
            if compressed:
                return (compressed,)
            type(self).USE_PIGZ = False

        return (gzip.compress(data, compresslevel=9, mtime=0),)

    @staticmethod
    def compress_using_pigz(data: bytes) -> bytes | None:
        """Compress better."""
        if not (pigz := shutil.which("pigz")):
            return None

        result = subprocess.run(  # nosec: B603
            [pigz, "-11", "--no-time", "--to-stdout", "-"],
            check=False,
            capture_output=True,
            input=data,
        )

        if result.returncode:
            return None

        return result.stdout

    @classmethod
    @override
    def file_extension(cls) -> str:
        """Return the file extension of the compressed files.

        e.g.: 'gz'
        """
        return "gz"


class ZstdFileCompressor(FileCompressor):
    """Compress files using Zstd compression."""

    @override
    def compress_bytes(self, data: bytes) -> Iterable[bytes]:
        """Compress bytes."""
        # pylint: disable-next=import-outside-toplevel,import-error
        import zstd  # type: ignore[import-not-found]

        return (zstd.compress(data, 22),)

    @classmethod
    @override
    def file_extension(cls) -> str:
        """Return the file extension of the compressed files.

        e.g.: 'zst'
        """
        return "zst"


def compress_dir(
    dir_: Path, compressors: Sequence[FileCompressor]
) -> Iterable[CompressionResult]:
    """Compress a directory."""
    assert dir_.is_dir(), "needs to be a directory"
    compressed_extensions = frozenset(c.file_extension() for c in compressors)
    for file in dir_.rglob("*"):
        if not file.is_file():
            continue
        if file.suffix.removeprefix(".") in compressed_extensions:
            continue
        for compressor in compressors:
            if compressed := compressor.compress(file):
                yield compressed


def get_static_dirs() -> Iterable[Path]:
    """Get the directories containing the static files."""
    source_dir = Path(__file__).absolute().parent.parent / "an_website"
    yield source_dir / "static"
    yield source_dir / "soundboard" / "files"


def get_compressors() -> Sequence[FileCompressor]:
    """Get the available compressors."""
    return ZstdFileCompressor(), GzipFileCompressor()


def compress_static_files() -> Iterable[CompressionResult]:
    """Compress static files."""
    compressors = get_compressors()

    for static_dir in get_static_dirs():
        yield from compress_dir(static_dir, compressors)


def clean_files() -> Iterable[Path]:
    """Delete compressed static files."""
    compressed_extensions = frozenset(
        c.file_extension() for c in get_compressors()
    )
    for static_dir in get_static_dirs():
        for file in static_dir.rglob("*"):
            if not file.is_file():
                continue
            if file.suffix.removeprefix(".") not in compressed_extensions:
                continue
            file.unlink()
            yield file


def main() -> None:
    """Compress static files."""
    cwd = Path.cwd().absolute()

    if "--clean" in sys.argv[1:]:
        for file in clean_files():
            print(
                f"Deleting ./{file.relative_to(cwd, walk_up=True)}",
                file=sys.stderr,
            )
        return

    for out_path, ratio, success in compress_static_files():
        print(
            f"./{out_path.relative_to(cwd, walk_up=True)}: {ratio:.2f}% {success}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
