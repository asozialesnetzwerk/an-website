from typing import List

from tornado.web import StaticFileHandler

from . import DIR

PATH = f"{DIR}/build/"
OPTIONS = {"path": PATH, "default_filename": "index.html"}


def get_handlers() -> List[tuple]:
    return [
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
    ]
