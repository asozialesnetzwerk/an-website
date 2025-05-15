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

"""A module with useful decorators."""

from __future__ import annotations

import contextlib
import logging
from base64 import b64decode
from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast, overload

from tornado.web import RequestHandler

from .token import InvalidTokenError, parse_token
from .utils import Permission, anonymize_ip

Default = TypeVar("Default")
Args = ParamSpec("Args")
Ret = TypeVar("Ret")


def keydecode(
    token: str,
    api_secrets: Mapping[str | None, Permission],
    token_secret: str | bytes | None,
) -> None | Permission:
    """Decode a key."""
    tokens: list[str] = [token]
    decoded: str | None
    try:
        decoded = b64decode(token).decode("UTF-8")
    except ValueError:
        decoded = None
    else:
        tokens.append(decoded)
    if token_secret:
        for _ in tokens:
            with contextlib.suppress(InvalidTokenError):
                return parse_token(_, secret=token_secret).permissions
    if decoded is None:
        return None
    return api_secrets.get(decoded)


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

    permissions: tuple[None | Permission, ...] = (  # TODO: CLEAN-UP THIS MESS!!
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
        (
            keydecode(
                inst.get_cookie("access_token", ""),
                keys,
                token_secret,
            )
            if allow_cookie_auth
            else None
        ),
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
    return_instead_of_finishing: Default,
    allow_cookie_auth: bool = True,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Ret | Default]]: ...


@overload
def requires(
    *perms: Permission,
    allow_cookie_auth: bool = True,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Ret]]: ...


def requires(
    *perms: Permission,
    return_instead_of_finishing: Any = _DefaultValue,
    allow_cookie_auth: bool = True,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Any]]:
    """Handle required permissions."""
    permissions = Permission(0)
    for perm in perms:
        permissions |= perm

    finish_with_error = return_instead_of_finishing is _DefaultValue

    def internal(method: Callable[Args, Ret]) -> Callable[Args, Any]:
        method.required_perms = permissions  # type: ignore[attr-defined]
        logger = logging.getLogger(f"{method.__module__}.{method.__qualname__}")

        wraps(method)

        @wraps(method)
        def wrapper(*args: Args.args, **kwargs: Args.kwargs) -> Any:
            instance = args[0]
            if not isinstance(instance, RequestHandler):
                raise TypeError(f"Instance has invalid type {type(instance)}")
            authorized = is_authorized(instance, permissions, allow_cookie_auth)
            if not authorized:
                if not finish_with_error:
                    return cast(Ret, return_instead_of_finishing)
                logger.warning(
                    "Unauthorized access to %s from %s",
                    instance.request.path,
                    anonymize_ip(instance.request.remote_ip),
                )
                instance.clear()
                instance.set_header("WWW-Authenticate", "Bearer")
                status = 401 if authorized is None else 403
                instance.set_status(status)
                instance.write_error(status, **kwargs)
                return None

            return method(*args, **kwargs)

        return wrapper

    return internal


@overload
def requires_settings(
    *settings: str,
    return_: Default,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Ret | Default]]: ...


@overload
def requires_settings(
    *settings: str,
    status_code: int,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Ret | None]]: ...


def requires_settings(
    *settings: str,
    return_: Any = _DefaultValue,
    status_code: int | None = None,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Any]]:
    """Require some settings to execute a method."""
    finish_with_error = return_ is _DefaultValue
    if not finish_with_error and isinstance(status_code, int):
        raise ValueError("return_ and finish_status specified")
    if finish_with_error and status_code is None:
        status_code = 503

    def internal(method: Callable[Args, Ret]) -> Callable[Args, Any]:
        logger = logging.getLogger(f"{method.__module__}.{method.__qualname__}")

        @wraps(method)
        def wrapper(*args: Args.args, **kwargs: Args.kwargs) -> Any:
            instance = args[0]
            if not isinstance(instance, RequestHandler):
                raise TypeError(f"Instance has invalid type {type(instance)}")
            missing = [
                setting
                for setting in settings
                if instance.settings.get(setting) is None
            ]
            if missing:
                if not finish_with_error:
                    return cast(Ret, return_)
                logger.warning(
                    "Missing settings %s for request to %s",
                    ", ".join(missing),
                    instance.request.path,
                )
                instance.send_error(cast(int, status_code))
                return None
            for setting in settings:
                kwargs[setting.lower()] = instance.settings[setting]
            return method(*args, **kwargs)

        return wrapper

    return internal


def get_setting_or_default(
    setting: str,
    default: Any,
) -> Callable[[Callable[Args, Ret]], Callable[Args, Ret]]:
    """Require some settings to execute a method."""

    def internal(method: Callable[Args, Ret]) -> Callable[Args, Ret]:
        @wraps(method)
        def wrapper(*args: Args.args, **kwargs: Args.kwargs) -> Ret:
            instance = args[0]
            if not isinstance(instance, RequestHandler):
                raise TypeError(f"Instance has invalid type {type(instance)}")
            kwargs[setting.lower()] = instance.settings.get(setting, default)
            return method(*args, **kwargs)

        return wrapper

    return internal
