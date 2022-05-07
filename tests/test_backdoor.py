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

import pickle
from typing import Any, Literal

from . import FetchCallable, app, assert_valid_response, fetch

assert fetch and app


async def request_and_parse(
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
    /,
    code: str,
    *,
    session: None | str = None,
    auth_key: None | str = None,
    mode: Literal["exec", "eval"] = "eval",
) -> dict[str, Any] | Any:
    """Make request to the backdoor and parse the response."""
    auth_key = "123qweQWE!@#000000000" if auth_key is None else auth_key
    headers = {"Authorization": auth_key}
    if session:
        headers["X-Backdoor-Session"] = session
    response = await fetch(
        f"/api/backdoor/{mode}",
        method="POST",
        headers=headers,
        body=code,
    )

    assert_valid_response(response, "application/vnd.python.pickle")

    unpickled = pickle.loads(response.body)

    if not isinstance(unpickled, dict):
        return unpickled

    assert len(unpickled) == 3
    assert isinstance(unpickled["success"], bool)
    assert isinstance(unpickled["output"], str)

    if unpickled["result"] is not None:
        assert isinstance(unpickled["result"], tuple)
        assert len(unpickled["result"]) == 2
        assert isinstance(unpickled["result"][0], str)
        if isinstance(unpickled["result"][1], bytes):
            result_list = list(unpickled["result"])
            result_list[1] = pickle.loads(result_list[1])
            unpickled["result"] = tuple(result_list)

    return unpickled


async def test_backdoor(  # pylint: disable=too-many-statements
    # pylint: disable=redefined-outer-name
    fetch: FetchCallable,
) -> None:
    """Test the backdoor."""
    response = await request_and_parse(fetch, "1 + 1")
    assert response["success"]
    assert not response["output"]
    assert response["result"] == ("2", 2)

    response = await request_and_parse(fetch, "print(2);", mode="eval")
    assert not response["success"]
    assert not response["output"]
    assert isinstance(response["result"][1], SyntaxError)

    response = await request_and_parse(fetch, "print(2);", mode="exec")
    assert response["success"]
    assert response["output"] == "2\n"
    assert not response["result"]

    response = await request_and_parse(fetch, "(x := 420)", session="123456789")
    assert response["success"]
    assert not response["output"]
    assert response["result"] == ("420", 420)

    response = await request_and_parse(fetch, "x", session="123456789")
    assert response["success"]
    assert not response["output"]
    assert response["result"] == ("420", 420)

    response = await request_and_parse(fetch, "_", session="123456789")
    assert response["success"]
    assert not response["output"]
    assert response["result"] == ("420", 420)

    response = await request_and_parse(fetch, "print")
    assert response["success"]
    assert not response["output"]
    assert response["result"][1] is print

    response = await request_and_parse(fetch, "help")
    assert response["success"]
    assert not response["output"]
    assert type(response["result"][1]) is type(help)

    response = await request_and_parse(fetch, "help")
    assert response["success"]
    assert not response["output"]
    assert type(response["result"][1]) is type(help)

    response = await request_and_parse(
        fetch, "(await self.load_session())['__name__']"
    )
    assert response["success"]
    assert not response["output"]
    assert response["result"] == ("'this'", "this")

    response = await request_and_parse(fetch, "_")
    assert not response["success"]
    assert not response["output"]
    assert response["result"][0].startswith("Traceback (most recent call last)")
    assert isinstance(response["result"][1], NameError)

    response = await request_and_parse(
        fetch, "raise SystemExit('x', 'y')", mode="exec"
    )
    assert isinstance(response, SystemExit)
    assert response.args == ("x", "y")

    # create something that cannot be pickled:
    response = await request_and_parse(
        fetch,
        "def fun():\n"
        "   class Result: pass\n"
        "   return Result\n"
        "LocalResult = fun()\n"
        "t = LocalResult()",
        mode="exec",
        session="tomato",
    )
    assert response["success"]
    assert not response["output"]
    assert response["result"] is None

    response = await request_and_parse(
        fetch, "raise SystemExit(t)", mode="exec", session="tomato"
    )
    assert isinstance(response, SystemExit)
    assert response.args[0].startswith("<this.fun.<locals>.Result object at ")
    assert response.args[0].endswith(">")

    response = await request_and_parse(fetch, "t", session="tomato")
    assert response["success"]
    assert not response["output"]
    assert response["result"][0].startswith(
        "<this.fun.<locals>.Result object at "
    )
    assert response["result"][0].endswith(">")
    assert response["result"][1] is None

    response = await request_and_parse(fetch, "raise ValueError()", mode="exec")
    assert not response["success"]
    assert not response["output"]
    assert response["result"][0].startswith("Traceback (most recent call last)")
    assert response["result"][1].args == tuple()
    assert isinstance(response["result"][1], ValueError)
