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

import email.utils
import os
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Final

import orjson as json
import regex

from ..utils.static_file_handling import hash_file
from ..utils.utils import name_to_id, replace_umlauts

DIR: Final = os.path.dirname(__file__)

with open(os.path.join(DIR, "info.json"), encoding="UTF-8") as file:
    info = json.loads(file.read())

# {"muk": "Marc-Uwe Kling", ...}
person_dict: dict[str, str] = info["personen"]
Person = Enum("Person", {**person_dict}, module=__name__)  # type: ignore[misc]

PERSON_SHORTS: tuple[str, ...] = tuple(person_dict.keys())

books: list[str] = []
chapters: list[str] = []
for book in info["bücher"]:
    books.append(book["name"])

    for chapter in book["kapitel"]:
        chapters.append(chapter["name"])


Book = Enum("Book", [*books], module=__name__)  # type: ignore[misc]
Chapter = Enum("Chapter", [*chapters], module=__name__)  # type: ignore[misc]


del books, chapters, person_dict


def mark_query(text: str, query: None | str) -> str:
    """Replace the instances of the query with itself in a div."""
    if not query:
        return text

    query = regex.sub("(ä|ae)", "(ä|ae)", query.lower())
    query = regex.sub("(ö|oe)", "(ö|oe)", query)
    query = regex.sub("(ü|ue)", "(ü|ue)", query)
    query = regex.sub("(ü|ue)", "(ü|ue)", query)

    for word in query.split(" "):
        text = regex.sub(
            word,
            lambda match: f'<div class="marked">{match[0]}</div>',
            text,
            regex.IGNORECASE,  # pylint: disable=no-member
        )

    return text


@dataclass(frozen=True, slots=True)
class Info:
    """Info class that is used as a base for HeaderInfo and SoundInfo."""

    text: str

    def to_html(
        self,
        fix_url_func: Callable[  # pylint: disable=unused-argument
            [str], str
        ] = lambda url: url,
        query: None | str = None,
    ) -> str:
        """Return the text of the info and mark the query."""
        return mark_query(self.text, query)


@dataclass(frozen=True, slots=True)
class HeaderInfo(Info):
    """A header with a tag and href to itself."""

    tag: str = "h1"
    type: type[Book | Chapter | Person] = Book

    def to_html(
        self,
        fix_url_func: Callable[[str], str] = lambda url: url,
        query: None | str = None,
    ) -> str:
        """
        Return an HTML element with the tag and the content of the HeaderInfo.

        The HTML element gets an id and a href with a # to
        itself based on the text content.
        """
        _id = name_to_id(self.text)
        text = (
            self.text  # no need to mark query if type
            # is  book as the book title is excluded from the search
            if self.type == Book
            else mark_query(self.text, query)
        )
        return (
            f'<{self.tag} id="{_id}">'
            f'{text}<a no-dynload href="#{_id}" class="header-id-link"></a>'
            f"</{self.tag}>"
        )


@dataclass(frozen=True, slots=True)
class SoundInfo(Info):
    """The information about a sound."""

    book: Book
    chapter: Chapter
    person: Person

    def contains(self, string: None | str) -> bool:
        """Check whether this sound info contains a given string."""
        if string is None:
            return False

        content = " ".join([self.chapter.name, self.person.value, self.text])
        content = replace_umlauts(content.lower())

        return not any(
            word not in content
            for word in replace_umlauts(string.lower()).split(" ")
        )

    def get_filename(self) -> str:
        """Parse the text to return the name of the file."""
        return regex.sub(
            r"[^a-z0-9_-]+",
            "",
            replace_umlauts(self.text.lower().replace(" ", "_")),
        )

    def get_text(self) -> str:
        """Parse the text to only return the quote."""
        return self.text.split("-", 1)[1]

    def to_html(
        self,
        fix_url_func: Callable[[str], str] = lambda url: url,
        query: None | str = None,
    ) -> str:
        """Parse the info to a list element with an audio element."""
        file = self.get_filename()  # pylint: disable=redefined-outer-name
        href = fix_url_func(f"/soundboard/{self.person.name}")
        path = f"files/{file}.mp3"
        file_url = f"/soundboard/{path}?v={hash_file(os.path.join(DIR, path))}"
        return (
            "<li>"
            f"<a href='{href}' class='a_hover'>"
            f"{mark_query(self.person.value, query)}"
            "</a>"
            ": »"
            f"<a no-dynload href='{file_url}' class='quote-a'>"
            f"{mark_query(self.get_text(), query)}"
            "</a>"
            "«"
            "<br>"
            "<audio controls>"
            f"<source src='{file_url}' type='audio/mpeg'>"
            "</audio>"
            "</li>"
        )

    def to_rss(self, url: None | str) -> str:
        """Parse the info to a RSS item."""
        filename = self.get_filename()
        rel_path = f"files/{filename}.mp3"
        abs_path = os.path.join(DIR, rel_path)
        file_size = os.path.getsize(abs_path)
        mod_time_since_epoch = os.path.getmtime(abs_path)
        # convert seconds since epoch to readable timestamp
        modification_time = email.utils.formatdate(mod_time_since_epoch, True)
        link = f"/soundboard/{rel_path}"
        text = self.get_text()
        if url is not None:
            link = url + link
        return (
            "<item>"
            "<title>"
            f"[{self.book.name} - {self.chapter.name}] "
            f"{self.person.value}: »{text}«"
            "</title>"
            f"<quote>{text}</quote>"
            f"<book>{self.book.name}</book>"
            f"<chapter>{self.chapter.name}</chapter>"
            f"<person>{self.person.value}</person>"
            f"<link>{link}</link>"
            f"<enclosure url='{link}' type='audio/mpeg' length='{file_size}'>"
            "</enclosure>"
            f"<guid>{filename}</guid>"
            f"<pubDate>{modification_time}</pubDate>"
            "</item>"
        )


all_sounds: list[SoundInfo] = []
main_page_info: list[Info] = []
PERSON_SOUNDS: Final[dict[str, list[SoundInfo]]] = {}

for book_info in info["bücher"]:
    book = Book[book_info["name"]]
    main_page_info.append(HeaderInfo(book.name, "h1", Book))

    for chapter_info in book_info["kapitel"]:
        chapter = Chapter[chapter_info["name"]]
        main_page_info.append(HeaderInfo(chapter.name, "h2", Chapter))

        for file_text in chapter_info["dateien"]:
            person_short = file_text.split("-")[0]
            person = Person[person_short]

            sound_info = SoundInfo(file_text, book, chapter, person)
            all_sounds.append(sound_info)
            main_page_info.append(sound_info)
            PERSON_SOUNDS.setdefault(person_short, []).append(sound_info)

# convert to tuple for immutability
ALL_SOUNDS: Final[tuple[SoundInfo, ...]] = tuple(all_sounds)
MAIN_PAGE_INFO: Final[tuple[Info, ...]] = tuple(main_page_info)

del all_sounds, main_page_info
