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

"""The random text API of the website."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import ClassVar

import regex

from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo
from . import DIR


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
    """The arguments for the random text API."""

    seed: str = ""
    words: int = 500

    def validate(self) -> None:
        """Validate this."""
        self.words = max(0, min(self.words, 2000))


WORDS = tuple(
    (DIR / "words.txt")
    .read_text(encoding="UTF-8")
    .replace("sozial", "asozial")
    .replace("Sozial", "Asozial")
    .splitlines()
)

HTML: str = (
    "<!DOCTYPE html>"
    '<html lang="de">'
    "<head>"
    "<title>{title}</title>"
    "</head>"
    "<body>"
    "<h1>{title}</h1>"
    "{text}"
    "</body>"
    "</html>"
)
HTML_BLOCKS: tuple[str, ...] = (
    "<blockquote>{p}</blockquote>",
    "<code>{p}</code>",
    "<pre>{p}</pre>",
)


def generate_random_word(random: Random, title: bool = False) -> str:
    """Generate a random word."""
    word = random.choice(WORDS)
    return word.title() if title else word


def generate_random_text(random: Random, length: int, end: str = "") -> str:
    """Generate a random text."""
    text: list[str] = []

    title_next = True

    for _ in range(length - 1):
        text.append(generate_random_word(random, title=title_next))
        add_punctuation = not random.randrange(9) and not title_next
        title_next = False
        if add_punctuation:
            text.append(random.choice(".?!.?!,;"))
            if text[-1] not in ",;":
                title_next = True
                if not random.randrange(4):
                    text.append("\n\n")
                    continue
        text.append(" ")

    text.extend((generate_random_word(random, title=title_next), end))

    return "".join(text)


class RandomText(APIRequestHandler):
    """The request handler for the random text API."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = (
        "text/plain",
        "text/html",
    )

    @parse_args(type_=Arguments, validation_method="validate")
    async def get(self, args: Arguments, *, head: bool = False) -> None:
        """Handle GET requests to the random text API."""
        # pylint: disable=unused-argument
        random = Random(args.seed or None)
        text = generate_random_text(random, args.words, end=".")
        if self.content_type == "text/plain":
            return await self.finish(text)

        title = regex.sub(
            r"[.?!,;]*\s+",
            " ",
            generate_random_text(random, random.randint(2, 4)),
        )
        text = "".join(
            (
                f"<p>{paragraph}</p>"
                if random.randrange(3)
                else random.choice(HTML_BLOCKS).format(p=paragraph)
            )
            for paragraph in text.split("\n\n")
        )
        return await self.finish(HTML.format(title=title, text=text))
