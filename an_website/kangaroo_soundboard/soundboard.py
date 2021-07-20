from __future__ import annotations, barry_as_FLUFL

from typing import List

from tornado.web import HTTPError, StaticFileHandler

from ..utils.utils import BaseRequestHandler, ModuleInfo, PageInfo
from . import (
    ALL_SOUNDS,
    DIR,
    MAIN_PAGE_INFO,
    PERSON_SOUNDS,
    HeaderInfo,
    Info,
    Person,
)


def get_module_info() -> ModuleInfo:
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
                r"/kaenguru-soundboard/([^./]+)"
                r"(\.html|\.htm|/|/index.html|/index.htm)?",
                SoundboardHtmlHandler,
            ),
            (
                r"/kaenguru-soundboard(/?)",
                SoundboardHtmlHandler,
            ),
        ),
        (
            PageInfo(
                "Känguru-Soundboard-Suche",
                "Durchsuche das Känguru-Soundboard",
                "/kaenguru-soundboard/suche",
            ),
            PageInfo(
                "Känguru-Soundboard nach Personen sortiert",
                "Das Känguru-Soundboard mit Sortierung nach Personen",
                "/kaenguru-soundboard/personen",
            ),
        ),
    )


class SoundboardRssHandler(BaseRequestHandler):
    async def get(self, path, _end=None):  # pylint: disable=unused-argument
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

        raise HTTPError(404, reason="Feed not found")


class SoundboardHtmlHandler(BaseRequestHandler):
    async def get(self, path, _end=None):  # pylint: disable=unused-argument
        if path is not None:
            path = path.lower()
        if path in (None, "", "index", "/"):
            return self.render(
                "pages/soundboard.html",
                sound_info_list=MAIN_PAGE_INFO,
                query=None,
            )
        if path in ("persons", "personen"):
            persons_list: List[Info] = []
            for _k, person_sounds in PERSON_SOUNDS.items():
                persons_list.append(HeaderInfo(Person[_k].value))
                persons_list += person_sounds
            return self.render(
                "pages/soundboard.html",
                sound_info_list=persons_list,
                query=None,
            )
        if path in ("search", "suche"):
            query = self.get_query_argument("q", "")
            found: List[Info] = []
            for sound_info in ALL_SOUNDS:
                if sound_info.contains(query):
                    found.append(sound_info)

            return self.render(
                "pages/soundboard.html", sound_info_list=found, query=query
            )

        if path in PERSON_SOUNDS:
            return self.render(
                "pages/soundboard.html",
                sound_info_list=(
                    [HeaderInfo(Person[path].value)] + PERSON_SOUNDS[path]
                ),
                query=None,
            )

        raise HTTPError(404, reason="Page not found")
