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

"""The tests for the background tasks."""

import asyncio
from datetime import datetime, timedelta
from itertools import repeat

import time_machine
from time_machine import travel
from tornado.web import Application
from typed_stream._impl import Stream

from an_website import EVENT_SHUTDOWN
from an_website.utils.background_tasks import start_background_tasks

from . import app


@travel(datetime.now(), tick=True)
async def test_start_background_tasks_without_tasks(app: Application):
    bg_tasks = start_background_tasks(
        app=app,
        processes=0,
        module_infos=[],
        loop=asyncio.get_running_loop(),
        worker=None,
        elasticsearch_is_enabled=False,
        redis_is_enabled=False,
        main_pid=1,
    )
    EVENT_SHUTDOWN.set()
    await asyncio.gather(*bg_tasks)
    EVENT_SHUTDOWN.clear()

    assert not bg_tasks
