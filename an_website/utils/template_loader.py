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

"""A Tornado template loader."""

from __future__ import annotations

import os.path
from importlib.resources.abc import Traversable
from typing import override

from tornado.template import BaseLoader, Template


class TemplateLoader(BaseLoader):
    """A Tornado template loader."""

    root: Traversable

    def __init__(self, root: Traversable, whitespace: None | str) -> None:
        """Initialize the template loader."""
        self.root = root
        super().__init__(whitespace=whitespace)

    @override
    def _create_template(self, name: str) -> Template:
        """Create a template from the given name."""
        return Template((self.root / name).read_bytes(), name=name, loader=self)

    @override
    def resolve_path(self, name: str, parent_path: str | None = None) -> str:
        """Resolve the template path.

        name is interpreted as relative to parent_path if it's not None.
        """
        if (
            # same check as in tornado.template.Loader
            parent_path
            and not parent_path.startswith("<")
            and not parent_path.startswith("/")
            and not name.startswith("/")
        ):
            return os.path.normpath(
                os.path.join(os.path.dirname(parent_path), name)
            )
        return name
