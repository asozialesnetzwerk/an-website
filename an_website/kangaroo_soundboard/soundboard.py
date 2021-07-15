from __future__ import annotations, barry_as_FLUFL

from typing import List

from tornado.web import HTTPError, StaticFileHandler

from ..utils.utils import BaseRequestHandler, ModuleInfo
from . import (
    ALL_SOUNDS,
    DIR,
    MAIN_PAGE_INFO,
    PERSON_SOUNDS,
    HeaderInfo,
    Info,
    Person,
)

PATH = f"{DIR}/"  # folder with all pages of the page


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (
                r"/kaenguru-soundboard/(.*mp3)",
                StaticFileHandler,
                {"path": PATH, "default_filename": "index.html"},
            ),
            (
                r"/kaenguru-soundboard/(.*)(\.rss|\.xss|/feed|/feed.rss)",
                SoundboardRssHandler,
            ),
            (
                r"/kaenguru-soundboard/()(feed|feed.rss)",
                SoundboardRssHandler,
            ),
            (
                r"/kaenguru-soundboard/([^./]*)(\.html|\.htm|/|/index.html|/index.htm)?",
                SoundboardHtmlHandler,
            ),
        ),
        name="Känguru-Soundboard",
        description="Kurze Sounds aus den Känguru Chroniken",
        path="/kaenguru-soundboard/",  # the / at the end is important
    )


class SoundboardRssHandler(BaseRequestHandler):
    async def get(self, path, path_end):  # pylint: disable=unused-argument
        self.set_header("Content-Type", "text/xml")
        if path is None or len(path) == 0 or path == "index":
            return self.render(
                "rss/soundboard.xml", sound_info_list=ALL_SOUNDS
            )

        if path in PERSON_SOUNDS:
            return self.render(
                "rss/soundboard.xml", sound_info_list=PERSON_SOUNDS[path]
            )

        raise HTTPError(404, reason="Feed not found")


class SoundboardHtmlHandler(BaseRequestHandler):
    async def get(self, path, path_end):  # pylint: disable=unused-argument
        print(path, path_end)
        if path is None or len(path) == 0 or path == "index":
            return self.render(
                "pages/soundboard.html", sound_info_list=MAIN_PAGE_INFO
            )
        if path == "persons":
            persons_list: List[Info] = []
            for _k, person_sounds in PERSON_SOUNDS.items():
                persons_list.append(HeaderInfo(Person[_k].value))
                persons_list += person_sounds
            return self.render(
                "pages/soundboard.html", sound_info_list=persons_list
            )
        if path in PERSON_SOUNDS:
            return self.render(
                "pages/soundboard.html",
                sound_info_list=(
                    [HeaderInfo(Person[path].value)] + PERSON_SOUNDS[path]
                ),
            )

        raise HTTPError(404, reason="Page not found")
