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

"""The tests for the backdoor."""

from __future__ import annotations

import pickle  # nosec: B403
from collections.abc import Callable
from functools import partial
from types import EllipsisType
from typing import Any, Literal, TypedDict, cast

import dill  # type: ignore[import-untyped]  # nosec: B403
import jsonpickle  # type: ignore[import-untyped]

from . import (  # noqa: F401  # pylint: disable=unused-import
    FetchCallable,
    app,
    assert_valid_response,
    fetch,
)

Result = tuple[str, Any]  # tuple[str, bytes] before unpickling


class Response(TypedDict):  # noqa: D101
    # pylint: disable=missing-class-docstring
    success: bool | EllipsisType
    output: None | str
    result: None | Result | SystemExit


ErrorTuple = tuple[int, str]


async def _request_and_parse(
    # pylint: disable=redefined-outer-name, too-many-arguments
    fetch: FetchCallable,  # noqa: F811
    /,
    code: str,
    *,
    accept: str,
    loads: Callable[[bytes], Any],
    content_type: str | None = None,
    session: None | str = None,
    auth_key: None | str = None,
    mode: Literal["exec", "eval"] = "eval",
    features: None | str = None,
) -> Response | ErrorTuple | str | None:
    """Make a request to the backdoor and parse the response."""
    auth_key = "123qweQWE!@#000000000" if auth_key is None else auth_key
    headers = {"Authorization": auth_key, "Accept": accept}

    if session:
        headers["X-Backdoor-Session"] = session

    if features:
        headers["X-Future-Feature"] = features

    http_response = await fetch(
        f"/api/backdoor/{mode}",
        method="POST",
        headers=headers,
        body=code,
    )

    assert_valid_response(http_response, content_type or accept)

    response: Response | ErrorTuple | str | None = loads(http_response.body)

    assert isinstance(response, dict | tuple | str | None)

    if not isinstance(response, dict):
        if isinstance(response, tuple):
            assert len(response) == 2
            assert isinstance(response[0], int)
            assert isinstance(response[1], str)
        return response

    assert len(response) == 3
    assert isinstance(response["success"], bool | EllipsisType)
    assert isinstance(response["output"], None | str)
    assert isinstance(response["result"], None | tuple | SystemExit)
    if isinstance(response["result"], tuple):
        assert len(response["result"]) == 2
        assert isinstance(response["result"][0], str)
        assert isinstance(response["result"][1], bytes | None)
        if isinstance(response["result"][1], bytes):
            result = list(response["result"])
            result[1] = loads(result[1])
            response["result"] = cast(Result, tuple(result))

    return response


request_and_parse = partial(
    _request_and_parse,
    accept="*/*",
    content_type="application/vnd.uqfoundation.dill",
    loads=dill.loads,
)


async def test_backdoor(fetch: FetchCallable) -> None:  # noqa: F811
    """Test the backdoor."""
    # pylint: disable=too-many-statements
    for request in (
        partial(
            _request_and_parse,
            accept="*/*",
            content_type="application/vnd.uqfoundation.dill",
            loads=pickle.loads,  # nosec: B301
        ),
        partial(
            _request_and_parse,
            accept="application/vnd.uqfoundation.dill",
            loads=dill.loads,  # nosec: B301
        ),
        partial(
            _request_and_parse,
            accept="application/json",
            loads=partial(
                jsonpickle.loads, on_missing="error", classes=type(...)
            ),
        ),
    ):
        response = await request(fetch, "0==0")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert response["result"] == ("True", True)

        response = await request(fetch, "(0<>0)", features="barry_as_FLUFL")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert response["result"] == ("False", False)

        response = await request(fetch, "print('spam');", mode="eval")
        assert isinstance(response, dict)
        assert not response["success"]
        assert not response["output"]
        assert isinstance(response["result"], tuple)
        assert isinstance(response["result"][1], SyntaxError)

        response = await request(fetch, "print('spam');", mode="exec")
        assert isinstance(response, dict)
        assert response["success"]
        assert response["output"] == "spam\n"
        assert not response["result"]

        response = await request(fetch, "(spam := 'tasty')", session="bacon")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert response["result"] == ("'tasty'", "tasty")

        response = await request(fetch, "spam", session="bacon")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert response["result"] == ("'tasty'", "tasty")

        response = await request(fetch, "_", session="bacon")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert response["result"] == ("'tasty'", "tasty")

        response = await request(fetch, "print")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert isinstance(response["result"], tuple)
        assert response["result"][1] is print

        response = await request(fetch, "help")
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert isinstance(response["result"], tuple)
        assert type(response["result"][1]) is type(help)

        response = await request(
            fetch, "(await self.load_session())['__name__']"
        )
        assert isinstance(response, dict)
        assert response["success"]
        assert not response["output"]
        assert response["result"] == ("'this'", "this")

        response = await request(fetch, "_")
        assert isinstance(response, dict)
        assert not response["success"]
        assert not response["output"]
        assert isinstance(response["result"], tuple)
        assert response["result"][0].startswith(
            "Traceback (most recent call last)"
        )
        assert isinstance(response["result"][1], NameError)

        response = await request(
            fetch, "raise SystemExit('spam', 'eggs')", mode="exec"
        )
        assert isinstance(response, dict)
        assert response["success"] is ...
        assert not response["output"]
        assert isinstance(response["result"], SystemExit)
        assert response["result"].args == ("spam", "eggs")

        # # create something that cannot be pickled
        # response = await request(
        #     fetch,
        #     "def toast():\n"
        #     "   class Toast: pass\n"
        #     "   return Toast\n"
        #     "LocalToast = toast()\n"
        #     "t = LocalToast()",
        #     mode="exec",
        #     session="sausage",
        # )
        # assert isinstance(response, dict)
        # assert response["success"]
        # assert not response["output"]
        # assert response["result"] is None

        # response = await request(
        #     fetch, "raise SystemExit(t)", mode="exec", session="sausage"
        # )
        # assert isinstance(response, dict)
        # assert response["success"] is ...
        # assert not response["output"]
        # assert isinstance(response["result"], SystemExit)
        # assert (
        #     response["result"]
        #     .args[0]
        #     .startswith("<this.toast.<locals>.Toast object at ")
        # )
        # assert response["result"].args[0].endswith(">")

        # response = await request(fetch, "t", session="sausage")
        # assert isinstance(response, dict)
        # assert response["success"]
        # assert not response["output"]
        # assert response["result"][0].startswith(
        #     "<this.toast.<locals>.Toast object at "
        # )
        # assert response["result"][0].endswith(">")
        # assert response["result"][1] is None

        response = await request(fetch, "0 / 0", mode="exec")
        assert isinstance(response, dict)
        assert not response["success"]
        assert not response["output"]
        assert isinstance(response["result"], tuple)
        assert response["result"][0].startswith(
            "Traceback (most recent call last)"
        )
        assert response["result"][1].args == ("division by zero",)
        assert isinstance(response["result"][1], ZeroDivisionError)
