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

"""Check if redis is available."""

import dataclasses
import os
import traceback

import redis


@dataclasses.dataclass(frozen=True)
class RedisInfo:
    """Information about redis."""

    has_redis_cell: bool
    url: str
    connection_kwargs: dict[str, object]
    version: str


def redis_info() -> None | RedisInfo:
    """Check whether redis is running."""
    if not (redis_url := os.environ.get("REDIS_URL")):
        return None
    conn = redis.Redis.from_url(redis_url)

    has_redis_cell: bool
    try:
        conn.execute_command("CL.THROTTLE", "<key>", 1, 1, 1)
    except redis.exceptions.ResponseError:
        traceback.print_exc()
        has_redis_cell = False
    else:
        has_redis_cell = True

    return RedisInfo(
        has_redis_cell=has_redis_cell,
        url=redis_url,
        connection_kwargs=conn.get_connection_kwargs(),  # type: ignore[no-untyped-call]
        version=conn.info()["redis_version"],
    )
