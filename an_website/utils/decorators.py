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

"""The decorators module with useful decorators."""

from __future__ import annotations

import contextlib
import logging
from base64 import b64decode
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast, overload

from tornado.web import HTTPError, RequestHandler

from .token import InvalidTokenError, parse_token
from .utils import Permission, anonymize_ip

Ret = TypeVar("Ret")


def keydecode(
    token: str,
    api_secrets: dict[str | None, Permission],
    token_secret: str | bytes | None,
) -> None | Permission:
    """Decode a key."""
    if token_secret:
        with contextlib.suppress(InvalidTokenError):
            return parse_token(token, secret=token_secret).permissions
    try:
        return api_secrets.get(b64decode(token).decode("UTF-8"))
    except ValueError:
        return None


def is_authorized(
    inst: RequestHandler,
    permission: Permission,
    allow_cookie_auth: bool = True,
) -> None | bool:
    """Check whether the request is authorized."""
    keys: dict[str | None, Permission] = inst.settings.get(
        "TRUSTED_API_SECRETS", {}
    )
    token_secret: str | bytes | None = inst.settings.get("AUTH_TOKEN_SECRET")

    permissions: tuple[None | Permission, ...] = (
        *(
            (
                keydecode(_[7:], keys, token_secret)
                if _.lower().startswith("bearer ")
                else keys.get(_)
            )
            for _ in inst.request.headers.get_list("Authorization")
        ),
        *(
            keydecode(_, keys, token_secret)
            for _ in inst.get_arguments("access_token")
        ),
        *(keys.get(_) for _ in inst.get_arguments("key")),
        keydecode(
            cast(str, inst.get_cookie("access_token", "")), keys, token_secret
        )
        if allow_cookie_auth
        else None,
        keys.get(inst.get_cookie("key", None)) if allow_cookie_auth else None,
    )

    if all(perm is None for perm in permissions):
        return None

    result = Permission(0)
    for perm in permissions:
        if perm:
            result |= perm

    return permission in result


_DefaultValue = object()


@overload
def requires(
    *perms: Permission,
    return_instead_of_raising_error: Ret,
    allow_cookie_auth: bool = True,
) -> Callable[[Callable[..., Ret]], Callable[..., Ret]]:
    ...


@overload
def requires(
    *perms: Permission,
    allow_cookie_auth: bool = True,
) -> Callable[[Callable[..., Ret]], Callable[..., Ret]]:
    ...


def requires(
    *perms: Permission,
    return_instead_of_raising_error: Any = _DefaultValue,
    allow_cookie_auth: bool = True,
) -> Callable[[Callable[..., Ret]], Callable[..., Ret]]:
    """Handle required permissions."""
    permissions = Permission(0)
    for perm in perms:
        permissions |= perm

    def internal(method: Callable[..., Ret]) -> Callable[..., Ret]:
        method.required_perms = permissions  # type: ignore[attr-defined]
        logger = logging.getLogger(f"{method.__module__}.{method.__qualname__}")

        @wraps(method)
        def wrapper(instance: RequestHandler, *args: Any, **kwargs: Any) -> Ret:
            authorized = is_authorized(instance, permissions, allow_cookie_auth)
            if not authorized:
                if return_instead_of_raising_error is _DefaultValue:
                    logger.warning(
                        "Unauthorized access to %s from %s",
                        instance.request.path,
                        anonymize_ip(instance.request.remote_ip),
                    )
                    raise HTTPError(401 if authorized is None else 403)

                return cast(Ret, return_instead_of_raising_error)

            return method(instance, *args, **kwargs)

        return wrapper

    return internal
