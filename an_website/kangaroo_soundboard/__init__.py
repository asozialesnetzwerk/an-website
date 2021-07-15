from __future__ import annotations, barry_as_FLUFL

import os
import re
import shutil
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union

import orjson
from tornado import template

# pylint: disable=invalid-name

DIR = os.path.dirname(__file__)

RSS_STRING = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Kaenguru-Soundboard{extra_title}</title>
    <description>Ein Soundboard zu den Känguru Chroniken{extra_desc}</description>
    <language>de-de</language>
    <link>https://asozial.org/kaenguru-soundboard/{extra_link}</link>
    {items}
  </channel>
</rss>
"""

RSS_ITEM_STRING = """<item>
    <title>{title}</title>
    <link>https://asozial.org/kaenguru-soundboard/files/{file_name}.mp3</link>
    <enclosure url="https://asozial.org/kaenguru-soundboard/files/{file_name}.mp3"
                 type="audio/mpeg">
    <guid>{file_name}</guid>
</item>
"""

RSS_TITLE_STRING = "[{book}, {chapter}] {file_name}"


class Book(Enum):
    CHRONIKEN = "Die Känguru-Chroniken"
    MANIFEST = "Das Känguru-Manifest"
    OFFENBAHRUNG = "Die Känguru-Offenbarung"
    APOKRYPHEN = "Die Känguru-Apokryphen"


@dataclass
class Info:
    text: str

    def to_html() -> str:
        return self.text


@dataclass
class HeaderInfo(Info):
    tag: str = "h1"

    def to_html() -> str:
        _id = name_to_id(self.text)
        return (
            f"<{self.tag} id='{_id}'>"
            f"<a href='{_id}' class='{self.tag}-a'>"
            f"🔗 {self.text}</a>"
            f"</{self.tag}>"
        )


@dataclass
class SoundInfo(Info):
    file: str
    person: str
    book: Book
    chapter: str

    def to_html() -> str:
        person_name = self.person
        return (
            f"<li><a href='/kaenguru-soundboard/{self.person}' "
            f"class='a_hover'>{person_name}</a>"
            f":»<a href='/kaenguru-soundboard/{self.file}' "
            f"class='quote-a'>{self.text}</a>«<br>"
            f"<audio controls><source src='/kaenguru-soundboard/{self.file}' "
            f"type='audio/mpeg'></source></audio></li>"
        )


os.makedirs(f"{DIR}/build", exist_ok=True)
# Känguru-Chroniken.\"\n---\n"

with open(f"{DIR}/info.json", "r") as my_file:
    info = orjson.loads(my_file.read())


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


rss_items = ""
persons_rss: Dict[str, str] = {}

all_sounds: List[SoundInfo] = []
person_sounds: Dict[str, List[SoundInfo]] = {}
main_page_info: List[Info]

for book_info in info["bücher"]:
    book = Book(book_info["name"])

    main_page_info.append(HeaderInfo(book.value, "h1"))

    for chapter in book_info["kapitel"]:
        chapter_name = chapter["name"]

        for file_text in chapter["dateien"]:
            file = re.sub(
                r"[^a-z0-9_-]+",
                "",
                replace_umlauts(file_text.lower().replace(" ", "_")),
            )
            full_file = f"files/{file}.mp3"
            person = file_text.split("-")[0]

            audio_html = create_audio_el(full_file, file_text.split("-", 1)[1])

            persons_stuff[
                person
            ] = f"{persons_stuff.get(person, '')}\n{audio_html.to_html()}"

            audio_html.content = (
                create_anchor(person, persons[person]).to_html() + ":"
            )
            chapter_html.children.append(audio_html)
            # rss:
            title_file_name = (
                persons[file_text.split("-", 1)[0]]
                + ": »"
                + file_text.split("-", 1)[1]
                + "«"
            )
            rss = (
                RSS_ITEM_STRING.format(
                    title=RSS_TITLE_STRING.format(
                        book=book_name,
                        chapter=chapter_name.split(":")[0],
                        file_name=title_file_name,
                    ),
                    file_name=file,
                )
                + "\n"
            )
            rss_items += rss
            persons_rss[person] = persons_rss.get(person, "") + rss

        book_html.children.append(chapter_html)

    index_elements.append(book_html)


index_html = "\n\n".join(_el.to_html() for _el in index_elements)

parent_dir = os.path.dirname(DIR)
template_loader = template.Loader(f"{parent_dir}/templates/")
templ = template_loader.load("pages/soundboard.html")
base_url = "https://joshix.asozial.org/soundboard/"

# write main page:
with open(f"{DIR}/build/index.html", "w+") as main_page:
    main_page.write(
        index_html
        # HTML_STRING.format(
        #    extra_title="", extra_desc="", extra_link="", content=index_html
        # )
    )

persons_html = ""

# pages for every person:
for key in persons_stuff:  # pylint: disable=consider-using-dict-items
    _dir = f"{DIR}/build/" + replace_umlauts(key)
    os.makedirs(_dir, exist_ok=True)
    person = (
        persons[key]
        .replace("Das", "dem")
        .replace("Der", "dem")
        .replace("Die", "der")
    )
    content = "<h1>" + persons[key] + "</h1>" + persons_stuff[key]
    extra_title = " (Coole Sprüche/Sounds von " + person + ")"
    extra_desc = " mit coolen Sprüchen/Sounds von " + person
    with open(f"{_dir}/index.html", "w+") as person_page:
        person_page.write(
            content
            # HTML_STRING.format(
            #    extra_title=extra_title,
            #    extra_desc=extra_desc,
            #    extra_link=key,
            #    content=content,
            # )
        )

    # page with sounds sorted by persons:
    persons_html += (
        HtmlSection(
            tag="h1", id=name_to_id(persons[key]), content=persons[key]
        ).to_html()
        + persons_stuff[key]
    )

    # rss for every person:
    with open(f"{_dir}/feed.rss", "w+") as person_rss:
        person_rss.write(
            RSS_STRING.format(
                items=persons_rss[key],
                extra_title=extra_title,
                extra_desc=extra_desc,
                extra_link=key,
            )
        )

# write persons page:
with open(f"{DIR}/build/persons.html", "w+") as persons_page:
    persons_page.write(
        persons_html
        # HTML_STRING.format(
        #    extra_title="", extra_desc="", extra_link="", content=persons_html
        # )
    )

# write rss:
with open(f"{DIR}/build/feed.rss", "w") as feed:
    feed.write(
        RSS_STRING.format(
            items=rss_items, extra_title="", extra_desc="", extra_link=""
        )
    )

# copy files to build folder:
shutil.copytree(f"{DIR}/files", f"{DIR}/build/files", dirs_exist_ok=True)

# copy files to static path:
parent_dir = os.path.dirname(DIR)
