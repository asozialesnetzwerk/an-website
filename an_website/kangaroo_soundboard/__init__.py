import json
import os
import re
import shutil
from typing import Dict

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

RSS_ITEM_STRING = """    <item>
      <title>{title}</title>
      <link>https://asozial.org/kaenguru-soundboard/files/{file_name}.mp3</link>
      <enclosure url="https://asozial.org/kaenguru-soundboard/files/{file_name}.mp3"
                 type="audio/mpeg">
      <guid>{file_name}</guid>          
    </item>"""

RSS_TITLE_STRING = "[{book}, {chapter}] {file_name}"

HTML_STRING = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="theme-color" content="#8B0000">
    <meta property="og:url" content="https://asozial.org/kaenguru-soundboard/{extra_link}" />
    <meta property="og:type" content="website" />
    <title>Känguru-Soundboard{extra_title}</title>
    <meta property="og:title" content="Känguru-Soundboard{extra_title}" />
    <meta property="og:description" content="Ein Soundboard zu den Känguru Chroniken{extra_desc}" />
    <style>
        :root {{
            --red: #8B0000;
            --white: #fefefe;
            --light-grey: #9e9e9e;
            --grey: #242424;
            --black: #000;
            --dark-grey: #111111;
            --light-red: #f00;
            --light-blue: #00bfff;
            --blue: #00f;
        }}
        * {{
            color: var(--white);
            background-color: var(--black);
        }}
       
    </style>
</head>
<body>
<div id="container">{content}</div>
<footer style="
position: fixed;
bottom: 20px;
left: 50%;
transform: translateX(-50%);
text-align: center;
color: var(--white);
background-color: transparent;
">
  Mit Liebe gebacken 🖤
  <a style="color: var(--red); background-color: transparent;"
     href="https://github.com/asozialesnetzwerk">
    Asoziales Netzwerk: Sektion GitHub
  </a>
</footer>
</body>
</html>
"""

os.makedirs(f"{DIR}/build", exist_ok=True)
# Känguru-Chroniken.\"\n---\n"

with open(f"{DIR}/info.json", "r") as my_file:
    info = json.loads(my_file.read())


def replace_umlauts(text: str) -> str:
    return (
        text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    )


def name_to_id(val: str) -> str:
    return re.sub(r"[^a-zäöüß0-9-]", "", val.lower().replace(" ", "-"))


def create_anchor(
    href: str, inner_html: str, color: str = "var(--red)", classes: str = "a_hover"
) -> str:
    return (
        f"<a href='{href}' class='{classes}' style='color: {color};'>{inner_html}</a>"
    )


def create_heading(heading_type: str, text: str) -> str:
    el_id = name_to_id(text)
    return (
        f"<{heading_type} id='{el_id}'>"
        f"{create_anchor('#' + el_id, '🔗 ' + text)}"
        f"</{heading_type}>"
    )


rss_items = ""

persons_stuff: Dict[str, str] = {}
persons_rss: Dict[str, str] = {}
persons = info["personen"]
index_html = "<h1>Känguru-Soundboard:</h1>"
for book in info["bücher"]:
    book_name = book["name"]
    index_html += create_heading("h2", book_name)
    for chapter in book["kapitel"]:
        chapter_name = chapter["name"]
        index_html += create_heading("h3", chapter_name) + "<ul>"
        for file_text in chapter["dateien"]:
            file = re.sub(
                r"[^a-z0-9_-]+",
                "",
                replace_umlauts(file_text.lower().replace(" ", "_")),
            )
            full_file = f"files/{file}.mp3"
            person = file_text.split("-")[0]
            to_write = (
                f"»{create_anchor(full_file, file_text.split('-', 1)[1], 'var(--light-grey)')}"
                f"«<br><audio controls><source src='{full_file}' type='audio/mpeg'></audio>"
            )

            persons_stuff[
                person
            ] = f"{persons_stuff.get(person, '')}<li>{to_write}</li>"

            index_html += (
                f"<li>{create_anchor(person, persons[person], 'var(--light-red)')}"
                f": {to_write}</li>"
            )
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
        index_html += "</ul>"

# write main page:
with open(f"{DIR}/build/index.html", "w+") as main_page:
    main_page.write(
        HTML_STRING.format(
            extra_title="", extra_desc="", extra_link="", content=index_html
        )
    )

persons_html = "<h1>Känguru-Soundboard</h1>"

# pages for every person:
for key in persons_stuff:
    _dir = f"{DIR}/build/" + replace_umlauts(key)
    os.makedirs(_dir, exist_ok=True)
    person = (
        persons[key].replace("Das", "dem").replace("Der", "dem").replace("Die", "der")
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
            HTML_STRING.format(
                extra_title=extra_title,
                extra_desc=extra_desc,
                extra_link=key,
                content=content,
            )
        )

    # page with sounds sorted by persons:
    persons_html += create_heading("h2", persons[key]) + persons_stuff[key]

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
        HTML_STRING.format(
            extra_title="", extra_desc="", extra_link="", content=persons_html
        )
    )

# write rss:
with open(f"{DIR}/build/feed.rss", "w") as feed:
    feed.write(
        RSS_STRING.format(items=rss_items, extra_title="", extra_desc="", extra_link="")
    )

# copy files to build folder:
shutil.copytree(f"{DIR}/files", f"{DIR}/build/files", dirs_exist_ok=True)

# copy files to static path:
parent_dir = os.path.dirname(DIR)
