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

"""The ping API of the website."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import ClassVar

from . import DIR
from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/zufaelliger-text", RandomText),),
        name="Zufälliger Text",
        description="Generiere zu jedem Request einen zufälligen Text.",
        path="/api/zufaelliger-text",
        hidden=True,
    )


@dataclass(slots=True)
class Arguments:
    """The arguments for the example page."""

    seed: str = ""
    words: int = 500

    def validate(self) -> None:
        """Validate this."""
        self.words = max(0, min(self.words, 2000))


WORDS = tuple(
    Path(DIR, "words.txt")
    .read_text(encoding="UTF-8")
    .replace("sozial", "asozial")
    .replace("Sozial", "Asozial")
    .splitlines()
)

HTML = (
    "<!DOCTYPE html>"
    '<html lang="de">'
    "<head>"
    "<title>{title}</title>"
    "</head>"
    "<body>"
    "{text}"
    "</body>"
    "</html>"
)


def generate_random_word(random: Random) -> str:
    """Generate a random word."""
    return random.choice(WORDS)


def generate_random_text(random: Random, length: int, end: str = "") -> str:
    """Generate a random text."""
    text: list[str] = []

    for _ in range(length):
        word = generate_random_word(random)
        if random.random() < 0.1:
            word += random.choice(".?!,")
        text.append(word)

    return " ".join(text).removesuffix(end) + end


class RandomText(APIRequestHandler):
    """The request handler for the ping API."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "text/plain",
        "text/html",
    )

    @parse_args(type_=Arguments, validation_method="validate")
    async def get(self, args: Arguments, *, head: bool = False) -> None:
        """Handle GET requests to the ping API."""
        # pylint: disable=unused-argument
        random = Random(args.seed or None)
        text = generate_random_text(random, args.words, end=".")
        if self.content_type == "text/plain":
            return await self.finish(text)
        if self.content_type == "text/html":
            return await self.finish(
                HTML.format(
                    title=generate_random_text(random, 2),
                    text=text,
                )
            )
