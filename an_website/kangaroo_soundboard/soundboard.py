from __future__ import annotations, barry_as_FLUFL

import os

from tornado.web import HTTPError, StaticFileHandler

from ..utils.utils import BaseRequestHandler, ModuleInfo
from . import DIR, ALL_SOUNDS, MAIN_PAGE_INFO, PERSON_SOUNDS


PATH = f"{DIR}/"  # folder with all pages of the page
OPTIONS = {"path": PATH, "default_filename": "index.html"}


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (r"/kaenguru-soundboard/(.*mp3)", StaticFileHandler, OPTIONS),
            (
                r"/kaenguru-soundboard/(.*)(\.rss|\.xss|/feed|/feed.rss)",
                SoundboardRssHandler,
            ),
            (
                r"/kaenguru-soundboard(/)(feed|feed.rss)",
                SoundboardRssHandler,
            ),
            (
                r"/kaenguru-soundboard(/.*)?",
                SoundboardHtmlHandler,
            ),
        ),
        name="Känguru-Soundboard",
        description="Kurze Sounds aus den Känguru Chroniken",
        path="/kaenguru-soundboard/",  # the / at the end is important
    )


class SoundboardRssHandler(BaseRequestHandler):
    async def get(self, path, path_end):
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
    async def get(self, path_end):
        if path_end is None:
            path = PATH
        else:
            path = PATH + path_end

        if os.path.isdir(path):
            path = os.path.join(path, "index.html")

        path_html = path + ".html"
        if os.path.isfile(path_html):
            path = path_html

        if os.path.isfile(path):
            with open(path) as html_file:
                self.render("pages/soundboard.html", content=html_file.read())
        else:
            raise HTTPError(404, reason="Datei nicht gefunden.")
