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

"""The wiki with stuff about the AN."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import markdown
import yaml
from tornado.httpclient import HTTPError

from ..utils.request_handler import BaseRequestHandler
from ..utils.utils import ModuleInfo, PageInfo
from . import DIR


@dataclass(order=True, frozen=True)
class WikiPage:
    """Class with information about a wiki page."""

    title: Optional[str]
    description: Optional[str]
    html: str
    keywords: tuple[str, ...]


def create_paths_dict() -> dict[str, WikiPage]:
    """
    Create the paths dict and return it.

    The paths dict is a dict with the relative path as key corresponding to
    the absolute path in the file system as value.
    """
    files_dir = os.path.join(DIR, "files")

    test: list[tuple[str, list[str]]] = [
        (root, files) for root, dirs, files in os.walk(files_dir)
    ]

    paths: dict[str, WikiPage] = {}
    for root, files in test:
        for file in files:
            if file.endswith(".md"):
                path = f"{root}/{file}"

                with open(path, encoding="utf-8") as md_file:
                    file_content = md_file.read()
                    yaml_header: Optional[str]
                    if file_content.startswith("---"):
                        empty, yaml_header, md_body = file_content.split(
                            "---", 2
                        )
                        del empty
                    else:
                        yaml_header = None
                        md_body = file_content

                info = (
                    None
                    if yaml_header is None
                    else yaml.safe_load(yaml_header)
                )

                wiki_page = WikiPage(
                    None
                    if info is None or "title" not in info
                    else str(info.get("title")),
                    None
                    if info is None
                    or "description"
                    not in info  # pylint: disable=unsupported-membership-test
                    else str(info.get("description")),
                    markdown.markdown(md_body),
                    tuple()
                    if info is None or "keywords" not in info
                    else tuple(
                        str(keyword) for keyword in info.get("keywords")
                    ),
                )

                paths[
                    path.removeprefix(files_dir).removesuffix(".md")
                ] = wiki_page
                if root == files_dir:
                    paths["/"] = wiki_page
                    paths[""] = wiki_page

    return paths


PATHS = create_paths_dict()


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    sub_pages_list: list[PageInfo] = []
    for optional_page_info in (
        PageInfo(
            name=str(wiki_page.title),
            description=str(wiki_page.description),
            path=f"/wiki{path}",
        )
        if wiki_page.title is not None
        else None
        for path, wiki_page in PATHS.items()
    ):
        if optional_page_info is not None:
            sub_pages_list.append(optional_page_info)

    return ModuleInfo(
        handlers=(
            (
                r"/wiki(/?.*)(.html?|/index.html)?",
                WikiHandler,
            ),
        ),
        name="Asoziales Wiki",
        description="Ein Wiki mit Sachen des Asozialen Netzwerkes.",
        path="/wiki",
        sub_pages=tuple(sub_pages_list),
    )


class WikiHandler(BaseRequestHandler):
    """The request handler for the wiki page."""

    async def get(
        self,
        path: str,
        file_suffix: str = "",  # pylint: disable=unused-argument
    ):
        """Handle the get requests to the wiki page."""
        info: Optional[WikiPage] = None

        if path in PATHS:
            info = PATHS.get(path)

        if info is None:
            raise HTTPError(404)

        if info.title is None:
            return self.render(
                "pages/wiki.html",
                content=info.html,
            )
        return self.render(
            "pages/wiki.html",
            content=info.html,
            title=info.title,
            description=info.description,
        )
