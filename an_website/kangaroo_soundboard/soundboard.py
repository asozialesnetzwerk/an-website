from __future__ import annotations, barry_as_FLUFL

from tornado.web import HTTPError, StaticFileHandler

import os

from ..utils.utils import BaseRequestHandler, ModuleInfo
from . import DIR

PATH = f"{DIR}/build"  # folder with all pages of the page
OPTIONS = {"path": PATH, "default_filename": "index.html"}


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (r"/kaenguru-soundboard/(.*mp3)", StaticFileHandler, OPTIONS),
            (r"/känguru-soundboard/(/.*mp3)", StaticFileHandler, OPTIONS),
            (r"/k%C3%A4nguru-soundboard/(.*mp3)", StaticFileHandler, OPTIONS),
            (r"/soundboard/(.*mp3)", StaticFileHandler, OPTIONS),
            (r"/kaenguru-soundboard/(.*rss)", StaticFileHandler, OPTIONS),
            (r"/känguru-soundboard/(/.*rss)", StaticFileHandler, OPTIONS),
            (r"/k%C3%A4nguru-soundboard/(.*rss)", StaticFileHandler, OPTIONS),
            (r"/soundboard/(.*rss)", StaticFileHandler, OPTIONS),
            (
                r"/kaenguru-soundboard(/.*)?",
                SoundboardHandler,
            ),
            (
                r"/känguru-soundboard(/.*)?",
                SoundboardHandler,
            ),
            (
                r"/k%C3%A4nguru-soundboard(/.*)?",
                SoundboardHandler,
            ),
            (
                r"/soundboard(/.*)?",
                SoundboardHandler,
            ),
        ),
        name="Känguru-Soundboard",
        description="Kurze Sounds aus den Känguru Chroniken",
        path="/kaenguru-soundboard/",  # the / at the end is important
    )


class SoundboardHandler(BaseRequestHandler):
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
