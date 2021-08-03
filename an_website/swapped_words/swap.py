"""Page that swaps words."""
from __future__ import annotations

from ..utils.utils import BaseRequestHandler, ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/vertauschte-woerter/?", SwappedWords),
            (r"/swapped-words/?", SwappedWords),
        ),
        name="Vertauschte Wörter",
        description="Eine Seite, die Wörter vertauscht",
        path="/vertauschte-woerter",
    )


class SwappedWords(BaseRequestHandler):
    """The request handler for the swapped words page."""

    def get(self):
        """Handle get requests to the swapped words page."""
        text = self.get_query_argument("text", default="")
        self.render("pages/swapped_words.html", text=text, output=text.upper())
