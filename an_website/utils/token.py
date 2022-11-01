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

"""A module providing special auth tokens."""

from __future__ import annotations

import hashlib
import hmac
import math
from base64 import b64decode, b64encode
from datetime import datetime
from typing import ClassVar, Literal, NamedTuple, TypeAlias, TypeGuard, get_args

from .utils import Permission

TokenVersion: TypeAlias = Literal["0"]
SUPPORTED_TOKEN_VERSIONS: tuple[TokenVersion, ...] = get_args(TokenVersion)


class ParseResult(NamedTuple):
    """The class representing a token."""

    token: str
    permissions: Permission
    valid_until: datetime
    salt: bytes


class InvalidTokenError(Exception):
    """Exception thrown for invalid or expired tokens."""


class InvalidTokenVersionError(InvalidTokenError):
    """Exception thrown when the token has an invalid version."""

    SUPPORTED_TOKEN_VERSIONS: ClassVar = SUPPORTED_TOKEN_VERSIONS


def is_supported_version(version: str) -> TypeGuard[TokenVersion]:
    """Check whether the argument is a supported token version."""
    return version in SUPPORTED_TOKEN_VERSIONS


def _split_token(token: str) -> tuple[TokenVersion, str]:
    """Split a token into version and the body of the token."""
    if not token:
        raise InvalidTokenError()

    version = token[0]
    if is_supported_version(version):
        return version, token[1:]

    raise InvalidTokenVersionError()


def parse_token(  # pylint: disable=inconsistent-return-statements
    token: str,
    *,
    secret: bytes | str,
    verify_time: bool = True,
) -> ParseResult:
    """Parse an auth-token."""
    secret_bytes = secret.encode("UTF-8") if isinstance(secret, str) else secret
    version, token_body = _split_token(token)
    try:
        if version == "0":
            return _parse_token_v0(
                token_body, secret_bytes, verify_time=verify_time
            )
    except InvalidTokenError:
        raise
    except Exception as exc:
        raise InvalidTokenError from exc


def create_token(
    permissions: Permission,
    *,
    secret: bytes | str,
    duration: int,
    start_time: datetime | None = None,
    salt: str | None | bytes = None,
    version: TokenVersion = SUPPORTED_TOKEN_VERSIONS[-1],
) -> ParseResult:
    """Create an auth token."""
    secret_bytes = secret.encode("UTF-8") if isinstance(secret, str) else secret
    start_date = datetime.now() if start_time is None else start_time
    salt_bytes = salt.encode("UTF-8") if isinstance(salt, str) else salt or b""
    token: str
    if version == "0":
        token = _create_token_body_v0(
            permissions, secret_bytes, duration, start_date, salt_bytes
        )

    return parse_token(version + token, secret=secret, verify_time=False)


def int_to_bytes(number: int, length: int, signed: bool = False) -> bytes:
    """Convert an int to bytes."""
    return number.to_bytes(length, "big", signed=signed)


def bytes_to_int(bytes_: bytes, signed: bool = False) -> int:
    """Convert an int to bytes."""
    return int.from_bytes(bytes_, "big", signed=signed)


def _parse_token_v0(
    token_body: str, secret: bytes, *, verify_time: bool = True
) -> ParseResult:
    """Parse an auth-token of version 0."""
    data: bytes = b64decode(token_body)
    data, hash_ = data[:-48], data[-48:]
    if not hmac.compare_digest(hmac.digest(secret, data, "SHA3-384"), hash_):
        raise InvalidTokenError()
    data, start_date = data[:-5], bytes_to_int(data[-5:])
    data, duration = data[:-5], bytes_to_int(data[-5:])
    permissions, salt = bytes_to_int(data[:-6]), data[-6:]

    now = int(datetime.now().timestamp())
    if verify_time and (now < start_date or start_date + duration < now):
        raise InvalidTokenError()

    return ParseResult(
        "0" + token_body,
        Permission(permissions),
        datetime.fromtimestamp(start_date + duration),
        salt,
    )


def _create_token_body_v0(
    permissions: Permission,
    secret: bytes,
    duration: int,
    start_date: datetime,
    salt: bytes,
) -> str:
    """Create an auth-token of version 0."""
    if not salt:
        salt = hashlib.blake2s(
            int_to_bytes(int(start_date.timestamp() - duration), 5)
        ).digest()[:6]
    elif len(salt) < 6:
        salt = b" " * (6 - len(salt)) + salt
    elif len(salt) > 6:
        salt = salt[:6]

    parts = (
        int_to_bytes(permissions, math.ceil(len(Permission) / 8)),
        salt,
        int_to_bytes(duration, 5),
        int_to_bytes(int(start_date.timestamp()), 5),
    )
    data: bytes = b"".join(parts)

    len_token = len(data) + 384 // 8
    if len_token % 3:
        data = int_to_bytes(0, 3 - (len_token % 3)) + data

    hash_ = hmac.digest(secret, data, "SHA3-384")
    return b64encode(data + hash_).decode("UTF-8")
