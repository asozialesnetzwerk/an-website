from __future__ import annotations, barry_as_FLUFL

from tornado.web import StaticFileHandler

from ..utils.utils import ModuleInfo
from . import DIR

PATH = f"{DIR}/build/"  # folder with all pages of the page
OPTIONS = {"path": PATH, "default_filename": "index.html"}


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (
                r"/kaenguru-soundboard/(.*)",
                StaticFileHandler,
                OPTIONS,
            ),
            (
                r"/känguru-soundboard/(.*)",
                StaticFileHandler,
                OPTIONS,
            ),
            (
                r"/k%C3%A4nguru-soundboard/(.*)",
                StaticFileHandler,
                OPTIONS,
            ),
            (
                r"/soundboard/(.*)",
                StaticFileHandler,
                OPTIONS,
            ),
        ),
        name="Känguru-Soundboard",
        description="Kurze Sounds aus den Känguru Chroniken",
        path="/kaenguru-soundboard/",  # the / at the end is important
    )
