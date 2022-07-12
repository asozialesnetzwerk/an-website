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
# pylint: disable=missing-function-docstring, unused-argument
# fmt: off

"""⠗⡰⠓"""

from __future__ import annotations

from codecs import CodecInfo, register


def encode(data: str, errors: str = "strict") -> tuple[bytes, int]:
    output = bytearray()
    for pos, char in enumerate(data):
        byte = ord(char) - 0x2800
        if not 0 <= byte <= 255:
            if errors == "ignore":
                continue
            raise UnicodeEncodeError(
                "braille",
                char,
                pos,
                pos + 1,
                "ordinal not in range(0x2800, 0x2900)",
            )
        output.append(byte)
    return bytes(output), len(data)


def decode(data: bytes, errors: str = "strict") -> tuple[str, int]:
    return "".join(chr(0x2800 + byte) for byte in data), len(data)


def morb() -> CodecInfo:
    """⡉⡔⠧⡓⠠⡍⡏⡒⡂⡉⡎⠧⠠⡔⡉⡍⡅"""
    return CodecInfo(
        name="braille",
        encode=encode,  # type: ignore[arg-type]
        decode=decode,  # type: ignore[arg-type]
    )


register(lambda codec: morb() if codec == "braille" else None)
