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
import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Type, Union

import orjson

DIR = os.path.dirname(__file__)

with open(f"{DIR}/info.json", "r", encoding="utf-8") as my_file:
    info = orjson.loads(my_file.read())

# {"muk": "Marc-Uwe Kling", ...}
person_dict: dict[str, str] = info["personen"]
Person = Enum("Person", {**person_dict}, module=__name__)  # type: ignore

PERSON_SHORTS: tuple[str, ...] = tuple(person_dict.keys())

books: list[str] = []
chapters: list[str] = []
for book in info["bücher"]:
    books.append(book["name"])

    for chapter in book["kapitel"]:
        chapters.append(chapter["name"])


Book = Enum("Book", [*books], module=__name__)  # type: ignore
Chapter = Enum("Chapter", [*chapters], module=__name__)  # type: ignore


del books, chapters, person_dict


def mark_query(text: str, query: Optional[str]) -> str:
    """Replace the instances of the query with itself in a div."""
    if query is None or query == "":
        return text

    query = re.sub("(ä|ae)", "(ä|ae)", query.lower())
    query = re.sub("(ö|oe)", "(ö|oe)", query)
    query = re.sub("(ü|ue)", "(ü|ue)", query)
    query = re.sub("(ü|ue)", "(ü|ue)", query)

    for word in query.split(" "):
        text = re.sub(
            word,
            lambda match: f'<div class="marked">{match.group()}</div>',
            text,
            flags=re.RegexFlag.IGNORECASE,
        )

    return text


@dataclass
class Info:
    """Info class that is used as a base for HeaderInfo and SoundInfo."""

    text: str

    def to_html(
        self,
        fix_url_func: Callable[  # pylint: disable=unused-argument
            [str], str
        ] = lambda url: url,
        query: Optional[str] = None,
    ) -> str:
        """Return the text of the info and mark the query."""
        return mark_query(self.text, query)


@dataclass
class HeaderInfo(Info):
    """A header with a tag and href to itself."""

    tag: str = "h1"
    type: Type[Union[Book, Chapter, Person]] = Book

    def to_html(
        self,
        fix_url_func: Callable[  # pylint: disable=unused-argument
            [str], str
        ] = lambda url: url,
        query: Optional[str] = None,
    ) -> str:
        """
        Return a html element with the tag and the content of the HeaderInfo.

        The html element gets a id and a href with a # to
        itself based on the text content.
        """
        _id = name_to_id(self.text)
        return (
            f"<{self.tag} id='{_id}'>"
            f"<a href='#{_id}' class='{self.tag}-a'>🔗 "
            + (
                self.text  # no need to mark query if type
                # is  book as the book title is excluded from the search
                if self.type == Book
                else mark_query(self.text, query)
            )
            + "</a></{self.tag}>"
        )


@dataclass
class SoundInfo(Info):
    """The information about a sound."""

    book: Book
    chapter: Chapter
    person: Person

    def get_text(self) -> str:
        """Parse the text to only return the quote."""
        return self.text.split("-", 1)[1]

    def get_file_name(self) -> str:
        """Parse the text to return the name of the file."""
        return re.sub(
            r"[^a-z0-9_-]+",
            "",
            replace_umlauts(self.text.lower().replace(" ", "_")),
        )

    def contains(self, _str: Optional[str]) -> bool:
        """Check whether this sound info contains a given string."""
        if _str is None:
            return False

        content = " ".join([self.chapter.name, self.person.value, self.text])
        content = replace_umlauts(content)

        for word in replace_umlauts(_str).split(" "):
            if word not in content:
                return False

        return True

    def to_html(
        self,
        fix_url_func: Callable[[str], str] = lambda url: url,
        query: Optional[str] = None,
    ) -> str:  # pylint: disable=unused-argument
        """Parse the info to a list element with a audio element."""
        file = self.get_file_name()
        href = fix_url_func(f"/kaenguru-soundboard/{self.person.name}")
        return (
            f"<li><a href='{href}' "
            f"class='a_hover'>{mark_query(self.person.value, query)}</a>"
            f": »<a href='/kaenguru-soundboard/files/{file}.mp3' "
            f"class='quote-a'>{mark_query(self.get_text(), query)}</a>"
            f"«<br><audio controls>"
            f"<source src='/kaenguru-soundboard/files/{file}.mp3' "
            f"type='audio/mpeg'></source></audio></li>"
        )

    def to_rss(self, url: Optional[str]) -> str:
        """Parse the info to a rss item."""
        file_name = self.get_file_name()
        path = f"/files/{file_name}.mp3"
        file_size = os.path.getsize(DIR + path)
        mod_time_since_epoch = os.path.getmtime(DIR + path)
        # Convert seconds since epoch to readable timestamp
        modification_time = email.utils.formatdate(mod_time_since_epoch, True)
        link = f"/kaenguru-soundboard{path}"
        text = self.get_text()
        if url is not None:
            link = url + link
        return (
            f"<item>\n"
            f"<title>[{self.book.name} - {self.chapter.name}] "
            f"{self.person.value}: »{text}«</title>\n"
            f"<quote>{text}</quote>\n"
            f"<book>{self.book.name}</book>\n"
            f"<chapter>{self.chapter.name}</chapter>\n"
            f"<person>{self.person.value}</person>\n"
            f"<link>{link}</link>\n"
            f"<enclosure url='{link}' type='audio/mpeg' "
            f"length='{file_size}'></enclosure>\n"
            f"<guid>{link}</guid>\n"
            f"<pubDate>{modification_time}</pubDate>\n"
            f"</item>"
        )


def replace_umlauts(text: str) -> str:
    """Make a string lower case and replace ä,ö,ü,ß."""
    return (
        text.lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def name_to_id(val: str) -> str:
    """Replace umlauts and whitespaces in a string so it is a valid html id."""
    return re.sub(
        r"-+",
        "-",
        re.sub(r"[^a-z0-9-]", "", replace_umlauts(val.replace(" ", "-"))),
    )


all_sounds: list[SoundInfo] = []
main_page_info: list[Info] = []
PERSON_SOUNDS: dict[str, list[SoundInfo]] = {}

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
ALL_SOUNDS: tuple[SoundInfo, ...] = tuple(all_sounds)
MAIN_PAGE_INFO: tuple[Info, ...] = tuple(main_page_info)

del all_sounds, main_page_info
