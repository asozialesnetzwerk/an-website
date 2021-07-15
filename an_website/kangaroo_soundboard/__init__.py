from __future__ import annotations, barry_as_FLUFL

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

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

    def to_html(self) -> str:
        return self.text


@dataclass
class HeaderInfo(Info):
    tag: str = "h1"

    def to_html(self) -> str:
        _id = name_to_id(self.text)
        return (
            f"<{self.tag} id='{_id}'>"
            f"<a href='{_id}' class='{self.tag}-a'>"
            f"🔗 {self.text}</a>"
            f"</{self.tag}>"
        )


@dataclass
class SoundInfo(Info):
    book: Book
    chapter: Chapter
    person: Person

    def get_file(self) -> str:
        return re.sub(
            r"[^a-z0-9_-]+",
            "",
            replace_umlauts(self.text.lower().replace(" ", "_")),
        )

    def to_html(self) -> str:
        file = self.get_file()
        return (
            f"<li><a href='/kaenguru-soundboard/{self.person.value}' "
            f"class='a_hover'>{self.person.name}</a>"
            f":»<a href='/kaenguru-soundboard/{file}' "
            f"class='quote-a'>{self.text}</a>«<br><audio controls>"
            f"<source src='/kaenguru-soundboard/files/{file}.mp3' "
            f"type='audio/mpeg'></source></audio></li>"
        )

    def to_rss(self) -> str:
        file = self.get_file()
        return file


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


all_sounds: List[SoundInfo] = []
person_sounds: Dict[str, List[SoundInfo]] = {}
main_page_info: List[Info] = []

for book_info in info["bücher"]:
    book = Book[book_info["name"]]
    main_page_info.append(HeaderInfo(book.name, "h1"))

    for chapter_info in book_info["kapitel"]:
        chapter = Chapter[chapter_info["name"]]
        main_page_info.append(HeaderInfo(chapter.name, "h2"))

        for file_text in chapter_info["dateien"]:
            person_short = file_text.split("-")[0]
            person = Person[person_short]

            sound_info = SoundInfo(file_text, book, chapter, person)

            all_sounds.append(sound_info)
            main_page_info.append(sound_info)
            person_sounds.setdefault(person_short, []).append(sound_info)
