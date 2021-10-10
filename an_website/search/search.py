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

"""The search page used to search the website."""

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo, PageInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/suche/", Search),),
        name="Suche",
        description="Seite zum Durchsuchen der Webseite.",
        aliases=("/search/",),
        keywords=("Suche",),
        path="/suche/",
        hidden=True,
    )


class Search(BaseRequestHandler):
    """The tornado request handler for the search page."""

    async def get(self):
        """Handle get requests to the search page."""
        query = self.get_query_argument("q", default="", strip=True)

        module_infos: list[
            tuple[float, ModuleInfo, list[tuple[float, PageInfo]]]
        ] = []

        for module_info in self.settings.get("MODULE_INFOS"):
            score = module_info.search(query)
            if score > 0:
                sub_pages = [
                    (score, sub_page)
                    for sub_page in module_info.sub_pages
                    if (score := sub_page.search(query)) > 0
                ]
                sub_pages.sort(reverse=True)
                module_infos.append((score, module_info, sub_pages))

        module_infos.sort(reverse=True)

        await self.render(
            "pages/search.html", query=query, module_infos=module_infos
        )
