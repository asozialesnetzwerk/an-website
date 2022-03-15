#!/usr/bin/env python3

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

from __future__ import annotations

import re
from xml.etree.ElementTree import parse

if __name__ == "__main__":  # noqa: C901
    # how to get the file:
    # download : https://dumps.wikimedia.org
    # /dewiktionary/latest/dewiktionary-latest-pages-meta-current.xml.bz2
    # extract the .xml file
    xml = parse("dewiktionary-20210920-pages-meta-current.xml")

    pre = "{http://www.mediawiki.org/xml/export-0.10/}"

    titles = set()

    for el in xml.iter():  # noqa: C901  # pylint: disable=too-complex
        if el.tag != f"{pre}text":
            continue
        # == ōrdo ({{Sprache|Latein}}) ==
        title_line = None
        # === {{Wortart|Substantiv|Latein}}, {{m}} ===
        info_line = None
        for _str in el.itertext():
            for line in _str.split("\n"):
                line = line.strip()
                if not line.startswith("==") or not line.endswith("=="):
                    # print("no == ... ==", len(line), line)
                    continue
                if line.startswith("===") and line.endswith("==="):
                    info_line = line[3:-3].strip()
                else:
                    title_line = line[2:-2].strip()

                if None not in (title_line, info_line):
                    break

        if None in (title_line, info_line):
            continue

        # print("t,i: ", title_line, info_line)

        title = None
        if title_line.endswith("|Deutsch}})"):  # type: ignore[union-attr]
            # len("({{Sprache|Deutsch}})") == 21
            title = title_line.split("(")[0].strip()  # type: ignore[union-attr]
        # elif "Deutsch" in title_line:
        # print(title_line)

        if title is None:
            continue
        if title.startswith("[") and title.startswith("]"):
            title = title[1:-1]
        if "|" not in info_line:  # type: ignore[operator]
            continue
        word_type = info_line.split("|")[1]  # type: ignore[union-attr]
        # print("title=", title, "; word_type=", word_type)
        if word_type not in (
            "Abkürzung",
            "Adjektiv",
            "Adverb",
            "Affix",
            "Antwortpartikel",
            "Artikel",
            "Buchstabe",
            "Demonstrativpronomen",
            "Eigenname",
            "Fokuspartikel",
            "Formel",
            "Gebundenes Lexem",
            "Geflügeltes Wort",
            "Gradpartikel",
            "Grußformel",
            "Indefinitpronomen",
            "Interjektion",
            "Interrogativadverb",
            "Interrogativpronomen",
            "Konjunktion",
            "Konjunktionaladverb",
            "Kontraktion",
            "Lokaladverb",
            "Merkspruch",
            "Modaladverb",
            "Modalpartikel",
            "Nachname",
            "Negationspartikel",
            "Numerale",
            "Onomatopoetikum",
            "Ortsnamengrundwort",
            "Partikel",
            "Personalpronomen",
            "Possessivpronomen",
            "Postposition",
            "Pronomen",
            "Pronominaladverb",
            "Präfix",
            "Präfixoid",
            "Präposition",
            "Pseudopartizip",
            "Redewendung",
            "Reflexivpronomen",
            "Relativpronomen",
            "Reziprokpronomen",
            "Sprichwort",
            "Straßenname",
            "Subjunktion",
            "Substantiv",
            "Suffix",
            "Suffixoid",
            "Temporaladverb",
            "Toponym",
            "Verb",
            "Vergleichspartikel",
            "Vorname",
            "Wiederholungszahlwort",
            "Wortverbindung",
            "Zahlklassifikator",
            "Zahlzeichen",
            "Zirkumposition",
        ):
            continue
        # fix string "[[text|test]] [[wort]] [[dies ist ein satz]] wörter"
        # to         "text wort dies ist ein satz wörter"
        title = re.sub(r"\[\[([^]|]+)(?:\|[^]]+)?]]", r"\1", title)
        titles.add(title)

    with open("output.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(titles))
        file.close()
