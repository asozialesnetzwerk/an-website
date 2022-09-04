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

"""A page with wrong quotes."""

from __future__ import annotations

import os
from typing import Final

from tornado.web import RedirectHandler

from ..utils.utils import ModuleInfo, PageInfo
from .create import CreatePage1, CreatePage2
from .generator import QuoteGenerator, QuoteGeneratorAPI
from .image import QuoteAsImage
from .info import AuthorsInfoPage, QuotesInfoPage
from .quote_of_the_day import (
    QuoteOfTheDayAPI,
    QuoteOfTheDayRedirect,
    QuoteOfTheDayRss,
)
from .quotes import QuoteAPIHandler, QuoteById, QuoteMainPage, QuoteRedirectAPI
from .share import ShareQuote

DIR: Final = os.path.dirname(__file__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/zitate", QuoteMainPage),
            # {1,10} is too much, but better too much than not enough
            (r"/zitate/([0-9]{1,10})-([0-9]{1,10})", QuoteById),
            (r"/zitate/([0-9]{1,10})", QuoteById),
            (
                r"/zitate/-([0-9]{1,10})",
                RedirectHandler,
                {"url": "/zitate/info/a/{0}"},
            ),
            (
                r"/zitate/([0-9]{1,10})-",
                RedirectHandler,
                {"url": "/zitate/info/z/{0}"},
            ),
            (  # /zitate/69-420.html shouldn't say "unsupported file extension"
                r"/zitate/([0-9]{1,10})-([0-9]{1,10}).html?",
                RedirectHandler,
                {"url": "/zitate/{0}-{1}"},
            ),
            (  # redirect to the new URL
                r"/zitate/([0-9]{1,10})-([0-9]{1,10})/image\.([a-zA-Z]{3,4})",
                RedirectHandler,
                {"url": "/zitate/{0}-{1}.{2}"},
            ),
            (
                r"/zitate/([0-9]{1,10})-([0-9]{1,10})\.([a-zA-Z]{3,4})",
                QuoteAsImage,
            ),
            (
                r"/zitate/([0-9]{1,10})()\.([a-zA-Z]{3,4})",
                QuoteAsImage,
            ),
            (  # redirect to the new URL (changed because of robots.txt)
                r"/zitate/([0-9]{1,10})-([0-9]{1,10})/share",
                RedirectHandler,
                {"url": "/zitate/share/{0}-{1}"},
            ),
            (r"/zitate/share/([0-9]{1,10})-([0-9]{1,10})", ShareQuote),
            (r"/api/zitate(/full|)", QuoteRedirectAPI),
            (
                r"/api/zitate/([0-9]{1,10})-([0-9]{1,10})(?:/full|)",
                QuoteAPIHandler,
            ),
            (
                r"/api/zitate/([0-9]{1,10})(?:/full|)",
                QuoteAPIHandler,
            ),
            # quotes creator
            (r"/zitate/erstellen", CreatePage1),
            (r"/zitate/create-wrong-quote", CreatePage2),
            # quote generator
            (r"/zitate/generator", QuoteGenerator),
            (r"/api/zitate/generator", QuoteGeneratorAPI),
            # quote of the day
            (r"/zitat-des-tages/feed", QuoteOfTheDayRss),
            (r"/zitat-des-tages", QuoteOfTheDayRedirect),
            (
                r"/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})",
                QuoteOfTheDayRedirect,
            ),
            (r"/api/zitat-des-tages", QuoteOfTheDayAPI),
            (
                r"/api/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})",
                QuoteOfTheDayAPI,
            ),
            (r"/api/zitat-des-tages/full", QuoteOfTheDayAPI),
            (
                r"/api/zitat-des-tages/([0-9]{4}-[0-9]{2}-[0-9]{2})/full",
                QuoteOfTheDayAPI,
            ),
            # author/quote info
            (r"/zitate/info/a/([0-9]{1,10})", AuthorsInfoPage),
            (r"/zitate/info/z/([0-9]{1,10})", QuotesInfoPage),
        ),
        name="Falsch zugeordnete Zitate",
        short_name="Falsche Zitate",
        description="Witzige, aber falsch zugeordnete Zitate",
        path="/zitate",
        aliases=("/z",),
        sub_pages=(
            PageInfo(
                name="Falsche-Zitate-Ersteller",
                description="Erstelle witzige falsch zugeordnete Zitate",
                path="/zitate/erstellen",
            ),
            PageInfo(
                name="Der Zitate-Generator",
                short_name="Zitate-Generator",
                description="Lasse falsch zugeordnete Zitate generieren",
                path="/zitate/generator",
                keywords=(
                    "Generator",
                    "Falsche Zitate",
                    "Falsch zugeordnete Zitate",
                ),
            ),
            PageInfo(
                name="Das Zitat des Tages",
                description="Jeden Tag ein anderes Zitat",
                path="/zitat-des-tages",
                keywords=(
                    "Zitate",
                    "Witzig",
                    "Känguru",
                ),
            ),
        ),
        keywords=(
            "falsch zugeordnet",
            "Zitate",
            "Witzig",
            "Känguru",
            "Marc-Uwe Kling",
            "falsche Zitate",
            "falsch zugeordnete Zitate",
        ),
    )
