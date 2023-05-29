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

"""Create the required stuff for the soundboard from the info in info.json."""

from __future__ import annotations

import os
from typing import Final

from tornado.web import RedirectHandler

from ..utils.static_file_handling import CachedStaticFileHandler
from ..utils.utils import ModuleInfo, PageInfo
from .soundboard import SoundboardHTMLHandler, SoundboardRSSHandler

DIR: Final = os.path.dirname(__file__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Känguru-Soundboard",
        short_name="Soundboard",
        description=(
            "Ein Soundboard mit coolen Sprüchen und Sounds aus den "
            "Känguru-Chroniken"
        ),
        path="/soundboard",
        keywords=("Soundboard", "Känguru", "Witzig", "Sprüche"),
        handlers=(
            (
                r"/soundboard/files/(.*mp3)",
                CachedStaticFileHandler,
                {"path": os.path.join(DIR, "files")},
            ),
            (
                r"/soundboard/feed",
                SoundboardRSSHandler,
            ),
            (
                r"/soundboard/feed\.(rss|xml)",
                RedirectHandler,
                {"url": "/soundboard/feed"},
            ),
            (  # redirect handler for legacy reasons
                r"/soundboard/k(ä|%C3%A4)nguru(/.+|)",
                RedirectHandler,
                {"url": "/soundboard/kaenguru{1}"},
            ),
            (
                r"/soundboard/([^./]+)/feed",
                SoundboardRSSHandler,
            ),
            (
                r"/soundboard/([^/]+)(\.(rss|xml)|/feed\.(rss|xml))",
                RedirectHandler,
                {"url": "/soundboard/{0}/feed"},
            ),
            (
                r"/soundboard",
                SoundboardHTMLHandler,
            ),
            (
                r"/soundboard/([^./]+)",
                SoundboardHTMLHandler,
            ),
        ),
        sub_pages=(
            PageInfo(
                name="Soundboard-Suche",
                description="Durchsuche das Soundboard",
                path="/soundboard/suche",
                keywords=("Suche",),
            ),
            PageInfo(
                name="Soundboard-Personen",
                description="Das Soundboard mit Sortierung nach Personen",
                path="/soundboard/personen",
                keywords=("Personen",),
            ),
        ),
        aliases=(
            "/kaenguru-soundboard",
            "/känguru-soundboard",
            "/k%C3%A4nguru-soundboard",
        ),
    )
