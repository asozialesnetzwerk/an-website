from __future__ import annotations, barry_as_FLUFL

from tornado.web import StaticFileHandler

from ..utils.utils import ModuleInfo
from . import DIR

PATH = f"{DIR}/build/"  # place with all build html files
OPTIONS = {"path": PATH, "default_filename": "index.html"}


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (
                r"/wiki/(.*)",
                StaticFileHandler,
                OPTIONS,
            ),
        ),
        name="Asoziales Wiki",
        description="Ein Wiki mit Sachen des Asozialen Netzwerkes.",
        path="/wiki/",  # the / at the end is important
    )
