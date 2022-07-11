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
# pylint: disable=arguments-renamed, line-too-long
# pylint: disable=missing-class-docstring, missing-function-docstring

"""⠗⡰⠓"""  # noqa: D400

from __future__ import annotations

from codecs import (
    Codec,
    CodecInfo,
    IncrementalDecoder,
    IncrementalEncoder,
    StreamReader,
    StreamWriter,
    register,
)


def encode(data: bytes, errors: str = "strict") -> str:  # noqa: D103
    # pylint: disable=unused-argument
    return "".join(chr(0x2800 + byte) for byte in data)


def decode(data: str, errors: str = "strict") -> bytes:  # noqa: D103
    output = bytearray()
    for pos, char in enumerate(data):
        byte = ord(char) - 0x2800
        if not 0 <= byte <= 255:
            if errors == "ignore":
                continue
            if ord(char) <= 0xFF:
                spam = f"\\x{ord(char):02x}"
            elif ord(char) <= 0xFFFF:
                spam = f"\\u{ord(char):04x}"
            else:
                spam = f"\\U{ord(char):08x}"
            raise ValueError(
                f"'braille' codec can't decode character '{spam}' "
                f"in position {pos}: ordinal not in range(0x2800, 0x2900)"
            )
        output.append(byte)
    return bytes(output)


class BrailleCodec(Codec):  # noqa: D101
    def encode(self, data: bytes, errors: str = "strict") -> tuple[str, int]:  # type: ignore[override]  # noqa: D103, B950
        return encode(data, errors), len(data)

    def decode(self, data: str, errors: str = "strict") -> tuple[bytes, int]:  # type: ignore[override]  # noqa: D103, B950
        return decode(data, errors), len(data)


class BrailleIncrementalEncoder(IncrementalEncoder):  # noqa: D101
    def encode(self, data: bytes, final: bool = False) -> str:  # type: ignore[override]  # noqa: D103, B950
        return encode(data, self.errors)


class BrailleIncrementalDecoder(IncrementalDecoder):  # noqa: D101
    def decode(self, data: str, final: bool = False) -> bytes:  # type: ignore[override]  # noqa: D103, B950
        return decode(data, self.errors)


class BrailleStreamWriter(BrailleCodec, StreamWriter):  # noqa: D101
    pass


class BrailleStreamReader(BrailleCodec, StreamReader):  # noqa: D101
    pass


def getregentry() -> CodecInfo:  # noqa: D103
    return CodecInfo(
        name="braille",
        encode=BrailleCodec().encode,  # type: ignore[arg-type]
        decode=BrailleCodec().decode,  # type: ignore[arg-type]
        incrementalencoder=BrailleIncrementalEncoder,
        incrementaldecoder=BrailleIncrementalDecoder,
        streamwriter=BrailleStreamWriter,
        streamreader=BrailleStreamReader,
        _is_text_encoding=False,
    )


register(lambda name: getregentry() if name == "braille" else None)
