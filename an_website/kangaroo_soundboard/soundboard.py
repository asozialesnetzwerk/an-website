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

"""Handle the requests for the kangaroo soundboard."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import cache

from tornado.web import HTTPError, RedirectHandler, StaticFileHandler

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo, PageInfo
from . import (
    ALL_SOUNDS,
    DIR,
    MAIN_PAGE_INFO,
    PERSON_SHORTS,
    PERSON_SOUNDS,
    HeaderInfo,
    Info,
    Person,
    SoundInfo,
)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Känguru-Soundboard",
        description="Ein Soundboard mit coolen Sprüchen und Sounds aus den "
        "Känguru-Chroniken",
        path="/kaenguru-soundboard/",
        keywords=("Soundboard", "Känguru", "Witzig", "Sprüche"),
        handlers=(
            (
                r"/kaenguru-soundboard/files/(.*mp3)",
                StaticFileHandler,
                {"path": f"{DIR}/files/"},
            ),
            (
                r"/kaenguru-soundboard/feed/",
                SoundboardRSSHandler,
            ),
            (
                r"/kaenguru-soundboard/feed\.(rss|xml)",
                RedirectHandler,
                {"url": "/kaenguru-soundboard/feed/"},
            ),
            (
                r"/kaenguru-soundboard/([^./]+)/feed/",
                SoundboardRSSHandler,
            ),
            (
                r"/kaenguru-soundboard/([^/]+)(\.(rss|xml)|/feed\.(rss|xml))",
                RedirectHandler,
                {"url": "/kaenguru-soundboard/{0}/feed/"},
            ),
            (
                r"/kaenguru-soundboard/",
                SoundboardHTMLHandler,
            ),
            (
                r"/kaenguru-soundboard/([^./]*)/",
                SoundboardHTMLHandler,
            ),
        ),
        sub_pages=(
            PageInfo(
                name="Soundboard-Suche",
                description="Durchsuche das Känguru-Soundboard",
                path="/kaenguru-soundboard/suche/",
                keywords=("Suche",),
            ),
            PageInfo(
                name="Soundboard-Personen",
                description="Das Känguru-Soundboard mit Sortierung nach "
                "Personen",
                path="/kaenguru-soundboard/personen/",
                keywords=("Personen",),
            ),
        ),
        aliases=(
            "/soundboard/",
            "/känguru-soundboard/",
            "/k%C3%A4nguru-soundboard/",
        ),
    )


@cache
def get_rss_str(path: str, protocol_and_host: str) -> None | str:
    """Return the RSS string for the given path."""
    if path is not None:
        path = path.lower()

    if path in (None, "/", str()):
        _infos: Iterable[SoundInfo] = ALL_SOUNDS
    elif path in PERSON_SOUNDS:
        _infos = PERSON_SOUNDS[path]
    else:
        return None
    return "\n".join(
        sound_info.to_rss(protocol_and_host) for sound_info in _infos
    )


class SoundboardRSSHandler(BaseRequestHandler):
    """The Tornado handler that handles requests to the RSS feeds."""

    async def get(self, path: str = "/") -> None:
        """Handle the GET request and generate the feed content."""
        rss_str = get_rss_str(
            path, f"{self.request.protocol}://{self.request.host}"
        )

        if rss_str is not None:
            self.set_header("Content-Type", "application/rss+xml")
            await self.render("rss/soundboard.xml", rss_str=rss_str)

        raise HTTPError(404, reason="Feed not found.")


async def search_main_page_info(
    check_func: Callable[[SoundInfo], bool],
    info_list: Iterable[Info] = MAIN_PAGE_INFO,
) -> list[Info]:
    """Get a info list based on the query and the check_func and return it."""
    found: list[Info] = []
    for info in info_list:
        if isinstance(info, SoundInfo):
            if check_func(info):
                found.append(info)
        elif isinstance(info, HeaderInfo):
            tag = info.tag
            while (  # pylint: disable=while-used
                len(found) > 0
                and isinstance(last := found[-1], HeaderInfo)
                and (
                    tag
                    in (
                        "h1",  # if it gets to h3 this doesn't work as
                        # then this should also be done for h2 when the ones
                        # before are h3
                        last.tag,
                    )
                )
            ):
                del found[-1]
            found.append(info)

    # pylint: disable=while-used
    while len(found) > 0 and isinstance(found[-1], HeaderInfo):
        del found[-1]

    return found


class SoundboardHTMLHandler(BaseRequestHandler):
    """The Tornado handler that handles requests to the HTML pages."""

    async def get(self, path: str = "/") -> None:
        """Handle the GET request and generate the page content."""
        if path is not None:
            path = path.lower()

        parsed_info = await self.parse_path(path)
        if parsed_info is None:
            raise HTTPError(404, reason="Page not found")

        await self.render(
            "pages/soundboard.html",
            sound_info_list=parsed_info[0],
            query=parsed_info[1],
        )

    async def parse_path(
        self, path: None | str
    ) -> None | tuple[Iterable[Info], None | str]:
        """Get a info list based on the path and return it with the query."""
        if path in (None, str(), "index", "/"):
            return MAIN_PAGE_INFO, None

        if path in {"persons", "personen"}:
            persons_list: list[Info] = []
            for _k, person_sounds in PERSON_SOUNDS.items():
                persons_list.append(HeaderInfo(Person[_k].value, type=Person))
                persons_list += person_sounds
            return persons_list, None

        if path in {"search", "suche"}:
            query = self.get_query_argument("q", default=str())
            if query is None or query == str():
                return MAIN_PAGE_INFO, query

            return (
                await search_main_page_info(lambda info: info.contains(query)),
                query,
            )

        if path in PERSON_SHORTS:
            person = Person[path]
            return (
                await search_main_page_info(
                    lambda info: info.person == person
                ),
                None,
            )

        return None
