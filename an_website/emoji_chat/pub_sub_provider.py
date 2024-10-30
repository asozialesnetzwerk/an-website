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

"""A provider of the Redis PubSub class."""

from __future__ import annotations

import logging
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, Final

from redis.asyncio.client import PubSub, Redis

from .. import EVENT_REDIS

LOGGER: Final = logging.getLogger(__name__)


@dataclass(slots=True)
class PubSubProvider:
    """Provide a PubSub object."""

    channels: Collection[str]
    settings: dict[str, Any]
    worker: int | None
    _ps: PubSub | None = None
    _redis: Redis[str] | None = None

    async def __call__(self) -> PubSub:
        """Get PubSub object."""
        if not self.settings.get("REDIS"):
            LOGGER.error("Redis not available on worker %s", self.worker)

        await EVENT_REDIS.wait()

        redis: Redis[str] = self.settings["REDIS"]

        if self._ps:
            if self._redis == redis:
                return self._ps
            LOGGER.info(
                "Closing old PubSub connection on worker %s", self.worker
            )
            await self._ps.close()

        self._ps = redis.pubsub()
        self._redis = redis
        await self._ps.subscribe(*self.channels)
        return self._ps
