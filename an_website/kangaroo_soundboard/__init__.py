from __future__ import annotations, barry_as_FLUFL

import email.utils
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import orjson

DIR = os.path.dirname(__file__)

with open(f"{DIR}/info.json", "r") as my_file:
    info = orjson.loads(my_file.read())

# {"muk": "Marc-Uwe Kling", ...}
persons: Dict[str, str] = info["personen"]
Person = Enum("Person", {**persons}, module=__name__)  # type: ignore

books: List[str] = []
chapters: List[str] = []
for book in info["bücher"]:
    books.append(book["name"])

    for chapter in book["kapitel"]:
        chapters.append(chapter["name"])


Book = Enum("Book", [*books], module=__name__)  # type: ignore
Chapter = Enum("Chapter", [*chapters], module=__name__)  # type: ignore


del books, chapters, persons


@dataclass
class Info:
    text: str

    def to_html(self, url_app: str) -> str:  # pylint: disable=unused-argument
        return self.text


@dataclass
class HeaderInfo(Info):
    tag: str = "h1"

    def to_html(self, url_app: str) -> str:  # pylint: disable=unused-argument
        _id = name_to_id(self.text)
        return (
            f"<{self.tag} id='{_id}'>"
            f"<a href='#{_id}' class='{self.tag}-a'>"
            f"🔗 {self.text}</a>"
            f"</{self.tag}>"
        )


@dataclass
class SoundInfo(Info):
    book: Book
    chapter: Chapter
    person: Person

    def get_text(self) -> str:
        return self.text.split("-", 1)[1]

    def get_file_name(self) -> str:
        return re.sub(
            r"[^a-z0-9_-]+",
            "",
            replace_umlauts(self.text.lower().replace(" ", "_")),
        )

    def contains(self, _str: str) -> bool:
        content = " ".join(
            [self.book.name, self.chapter.name, self.person.value, self.text]
        )
        content = replace_umlauts(content.lower())

        for word in _str.lower().split(" "):
            if word not in content:
                return False

        return True

    def to_html(self, url_app: str) -> str:
        file = self.get_file_name()
        return (
            f"<li><a href='/kaenguru-soundboard/{self.person.name}{url_app}' "
            f"class='a_hover'>{self.person.value}</a>"
            f": »<a href='/kaenguru-soundboard/files/{file}.mp3' "
            f"class='quote-a'>{self.get_text()}</a>«<br><audio controls>"
            f"<source src='/kaenguru-soundboard/files/{file}.mp3' "
            f"type='audio/mpeg'></source></audio></li>"
        )

    def to_rss(self, url: Optional[str]) -> str:
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
    return (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def name_to_id(val: str) -> str:
    return re.sub(
        r"-+",
        "-",
        re.sub(
            r"[^a-z0-9-]", "", replace_umlauts(val.lower().replace(" ", "-"))
        ),
    )


ALL_SOUNDS: List[SoundInfo] = []
MAIN_PAGE_INFO: List[Info] = []
PERSON_SOUNDS: Dict[str, List[SoundInfo]] = {}

for book_info in info["bücher"]:
    book = Book[book_info["name"]]
    MAIN_PAGE_INFO.append(HeaderInfo(book.name, "h1"))

    for chapter_info in book_info["kapitel"]:
        chapter = Chapter[chapter_info["name"]]
        MAIN_PAGE_INFO.append(HeaderInfo(chapter.name, "h2"))

        for file_text in chapter_info["dateien"]:
            person_short = file_text.split("-")[0]
            person = Person[person_short]

            sound_info = SoundInfo(file_text, book, chapter, person)
            ALL_SOUNDS.append(sound_info)
            MAIN_PAGE_INFO.append(sound_info)
            PERSON_SOUNDS.setdefault(person_short, []).append(sound_info)
