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

"""The tests for the token module."""

from __future__ import annotations

from datetime import datetime

import pytest

from an_website.utils.token import (  # pylint: disable=import-private-name
    InvalidTokenError,
    _create_token_body_v0,
    _parse_token_v0,
    bytes_to_int,
    create_token,
    int_to_bytes,
    parse_token,
)
from an_website.utils.utils import Permission


def test_token_v0() -> None:
    """Test the token creation."""
    result = create_token(Permission(1), secret=b"xyzzy", duration=9999)
    assert result.permissions == Permission(1)
    token = _create_token_body_v0(
        Permission(20),
        b"xyzzy",
        100,
        datetime.fromtimestamp(0),
        b"\x00\x00\x00\x00\x00*",  # 42
    )
    assert (
        token == "ABQAAAAAACoAAAAAZAAAAAAAVuGjEJjux2P8zah"  # nosec: B105
        "9SjQGkxCWn9Iaszr/qJJHJSMWoRPoVjQKa6/jKFWPdBehSL0K"
    )

    parsed = _parse_token_v0(token, b"xyzzy", verify_time=False)
    assert parsed.salt == b"\x00\x00\x00\x00\x00*"
    assert parsed.permissions == Permission(20)
    assert parsed.valid_until == datetime.fromtimestamp(100)

    with pytest.raises(InvalidTokenError):
        _parse_token_v0(token, b"xyzzy")  # expired

    with pytest.raises(InvalidTokenError):
        parse_token("0" + token, secret=b"xyzzy")

    with pytest.raises(InvalidTokenError):
        _parse_token_v0(token, b"hunter2", verify_time=False)


def test_int_to_bytes() -> None:
    """Test the int to bytes conversion."""
    assert int_to_bytes(0, 2) == b"\0" * 2
    assert int_to_bytes(0x20, 2) == b"\0 "
    assert int_to_bytes(0x2000, 2) == b" \0"


def test_bytes_to_int() -> None:
    """Test the bytes to int conversion."""
    assert bytes_to_int(b"\0") == 0  # pylint: disable=compare-to-zero
    assert bytes_to_int(b" ") == 0x20
    assert bytes_to_int(b"  ") == 0x2020
    assert bytes_to_int(b" \0") == 0x2000
