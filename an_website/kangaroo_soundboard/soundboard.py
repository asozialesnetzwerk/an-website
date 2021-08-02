"""Handle the requests for the kangaroo soundboard."""
from __future__ import annotations

from typing import Callable, Iterable, Optional

from tornado.web import HTTPError, StaticFileHandler

from ..utils.utils import BaseRequestHandler, ModuleInfo, PageInfo
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
        "Känguru-Soundboard",
        "Ein Soundboard mit coolen Sprüchen und Sounds aus den "
        "Känguru-Chroniken",
        "/kaenguru-soundboard",
        (
            (
                r"/kaenguru-soundboard/files/(.*mp3)",
                StaticFileHandler,
                {"path": f"{DIR}/files/"},
            ),
            (
                r"/kaenguru-soundboard/(.+)(\.rss|\.xss|/feed|/feed\.rss)",
                SoundboardRssHandler,
            ),
            (
                r"/kaenguru-soundboard(/)(feed|feed\.rss|feed\.xml|feed/)",
                SoundboardRssHandler,
            ),
            (
                r"/kaenguru-soundboard/([^./]+)(\.html?|/|/index.html?)?",
                SoundboardHtmlHandler,
            ),
            (
                r"/kaenguru-soundboard(/?)",
                SoundboardHtmlHandler,
            ),
        ),
        (
            PageInfo(
                "Suche",
                "Durchsuche das Känguru-Soundboard",
                "/kaenguru-soundboard/suche",
            ),
            PageInfo(
                "Personen",
                "Das Känguru-Soundboard mit Sortierung nach Personen",
                "/kaenguru-soundboard/personen",
            ),
        ),
    )


class SoundboardRssHandler(BaseRequestHandler):
    """The tornado handler that handles requests to the rss feeds."""

    async def get(self, path, _end=None):  # pylint: disable=unused-argument
        """Handle the get request and generate the feed content."""
        self.set_header("Content-Type", "application/xml")
        if path is not None:
            path = path.lower()
        if path in (None, "index", "/", ""):
            return self.render(
                "rss/soundboard.xml", sound_info_list=ALL_SOUNDS
            )

        if path in PERSON_SOUNDS:
            return self.render(
                "rss/soundboard.xml", sound_info_list=PERSON_SOUNDS[path]
            )

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
            while (
                len(found) > 0
                and isinstance(last := found[-1], HeaderInfo)
                and (
                    tag
                    in (
                        "h1",  # if it gets to h3 this doesn't work as
                        # then this should also be done for h2 when the ones
                        # before are h3
                        last.tag,  # type: ignore
                    )
                )
            ):
                del found[-1]
            found.append(info)

    while len(found) > 0 and isinstance(found[-1], HeaderInfo):
        del found[-1]

    return found


class SoundboardHtmlHandler(BaseRequestHandler):
    """The tornado handler that handles requests to the html pages."""

    async def get(self, path, _end=None):  # pylint: disable=unused-argument
        """Handle the get request and generate the page content."""
        if path is not None:
            path = path.lower()

        parsed_info = await self.parse_path(path)
        if parsed_info is None:
            raise HTTPError(404, reason="Page not found")

        return self.render(
            "pages/soundboard.html",
            sound_info_list=parsed_info[0],
            query=parsed_info[1],
        )

    async def parse_path(
        self, path
    ) -> Optional[tuple[Iterable[Info], Optional[str]]]:
        """Get a info list based on the path and return it with the query."""
        if path in (None, "", "index", "/"):
            return MAIN_PAGE_INFO, None

        if path in ("persons", "personen"):
            persons_list: list[Info] = []
            for _k, person_sounds in PERSON_SOUNDS.items():
                persons_list.append(HeaderInfo(Person[_k].value, type=Person))
                persons_list += person_sounds
            return persons_list, None

        if path in ("search", "suche"):
            query = self.get_query_argument("q", "")
            if query is None or query == "":
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
