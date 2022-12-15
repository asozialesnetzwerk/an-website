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

import logging
from collections.abc import Callable
from functools import wraps
from inspect import isfunction
from typing import Any, TypeVar

from tornado.web import HTTPError

from .base_request_handler import BaseRequestHandler
from .utils import Permission, anonymize_ip

Ret = TypeVar("Ret")


def requires(
    permissions: Permission,
) -> Callable[[Callable[..., Ret]], Callable[..., Ret]]:
    """Handle required permissions."""
    assert isinstance(permissions, Permission)

    def internal(method: Callable[..., Ret]) -> Callable[..., Ret]:
        assert isfunction(method)

        method.required_perms = permissions  # type: ignore[attr-defined]
        logger = logging.getLogger(f"{method.__module__}.{method.__qualname__}")

        @wraps(method)
        def wrapper(
            instance: BaseRequestHandler, *args: Any, **kwargs: Any
        ) -> Ret:
            assert isinstance(instance, BaseRequestHandler)

            if not (is_authorized := instance.is_authorized(permissions)):
                instance.auth_failed = True
                logger.warning(
                    "Unauthorized access to %s from %s",
                    instance.request.path,
                    anonymize_ip(instance.request.remote_ip),
                )
                raise HTTPError(401 if is_authorized is None else 403)

            return method(instance, *args, **kwargs)

        return wrapper

    return internal
