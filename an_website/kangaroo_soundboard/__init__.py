from __future__ import annotations, barry_as_FLUFL

import os
import re
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Union

import orjson

# pylint: disable=invalid-name

DIR = os.path.dirname(__file__)


@dataclass
class HtmlElement:
    tag: str = "div"
    content: Union[str, HtmlElement] = ""
    properties: Dict[str, str] = field(default_factory=dict)

    def get_content_str(self) -> str:
        if type(self.content) == HtmlElement:
            return self.content.to_html()
        return str(self.content)

    def get_properties_str(self) -> str:
        return " ".join(f"{_k}='{_v}'" for (_k, _v) in self.properties.items())

    def to_html(self) -> str:
        return (
            f"<{self.tag} {self.get_properties_str()}>"
            f"{self.get_content_str()}</{self.tag}>"
        )


@dataclass
class HtmlAudio(HtmlElement):
    tag: str = "li"
    anchor: HtmlElement = None
    source: HtmlElement = None

    def get_content_str(self) -> str:
        return (
            f"{super().get_content_str()}"
            f"»{self.anchor.to_html()}«<br>"
            f"<audio controls>{self.source.to_html()}</audio>"
        )


@dataclass
class HtmlSection(HtmlElement):
    tag: str = "h1"  # h1, h2, h3, ...
    id: str = ""  # unique id
    children: List[HtmlElement] = field(default_factory=list)

    def to_html(self) -> str:
        return (
            f"<{self.tag} id='{self.id}' {self.get_properties_str()}>"
            f"<a href='#{self.id}' class='{self.tag}-a'>"
            f"🔗 {self.get_content_str()}</a>"
            f"</{self.tag}"
            "\n".join(child.to_html() for child in self.children)
        )


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

RSS_ITEM_STRING = """    <item>
      <title>{title}</title>
      <link>https://asozial.org/kaenguru-soundboard/files/{file_name}.mp3</link>
      <enclosure url="https://asozial.org/kaenguru-soundboard/files/{file_name}.mp3"
                 type="audio/mpeg">
      <guid>{file_name}</guid>
    </item>"""

RSS_TITLE_STRING = "[{book}, {chapter}] {file_name}"


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


def create_anchor(
    href: str,
    inner_html: str,
    color: str = "var(--red)",
    classes: str = "a_hover",
) -> str:
    props: Dict[str, str] = {
        "href": href,
        "class": classes,
        "style": f"color: {color};",
    }
    return HtmlElement(tag="a", content=inner_html, properties=props).to_html()


def create_audio_el(file_name: str, text: str, content: str = "") -> HtmlAudio:
    anchor = HtmlElement(tag="a", content=text, properties={"href": file_name})
    source = HtmlElement(
        tag="source", properties={"src": file_name, "type": "audio/mpeg"}
    )
    return HtmlAudio(anchor=anchor, source=source, content=content)


rss_items = ""

persons_stuff: Dict[str, str] = {}
persons_rss: Dict[str, str] = {}
persons = info["personen"]

index_elements: List[HtmlSection] = []

for book in info["bücher"]:
    book_name = book["name"]
    book_html = HtmlSection(
        tag="h2", content=book_name, id=name_to_id(book_name)
    )
    index_elements.append(book_html)
    for chapter in book["kapitel"]:
        chapter_name = chapter["name"]
        chapter_html = HtmlSection(
            tag="h3", content=chapter_name, id=name_to_id(chapter_name)
        )
        book_html.children.append(chapter_html)
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

            audio_html.content = create_anchor(person, persons[person]) + ":"
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

index_html = "<h1>Känguru-Soundboard:</h1>" + "\n\n".join(
    _el.to_html() for _el in index_elements
)

# write main page:
with open(f"{DIR}/build/index.html", "w+") as main_page:
    main_page.write(
        index_html
        # HTML_STRING.format(
        #    extra_title="", extra_desc="", extra_link="", content=index_html
        # )
    )

persons_html = "<h1>Känguru-Soundboard</h1>"

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
    content = (
        "<h1>Känguru-Soundboard</h1><h2>"
        + persons[key]
        + "</h2>"
        + persons_stuff[key]
        .replace("(files/", "(../files/")
        .replace("src='files/", "src='../files/")
    )
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
    # TODO: persons_html += create_heading("h2", persons[key]) + persons_stuff[key]

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
