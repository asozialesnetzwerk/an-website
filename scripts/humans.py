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
# pylint: disable=consider-using-namedtuple-or-dataclass

"""Generates a humans.txt file."""

from __future__ import annotations

import re  # pylint: disable=preferred-module
import sys
from collections.abc import Mapping, MutableSequence, Reversible, Set
from os.path import dirname, normpath
from pathlib import Path
from random import Random
from subprocess import run  # nosec: B404
from typing import Final
from unicodedata import category

REPO_ROOT: Final[str] = dirname(dirname(normpath(__file__)))
HUMANS_TXT: Final[Path] = Path(REPO_ROOT, "an_website/static/humans.txt")

# edit these 3 and .mailmap to change humans.txt
BOTS: Final[Set[str]] = {"Bot", "ImgBotApp", "snyk-bot"}
MAINTAINERS: Final[Mapping[str, Mapping[str, str]]] = {
    "Joshix": {
        "Location": "NRW, Germany",
        "Email": "joshix@asozial.org",
        "__role": "Full-stack developer",
    },
    "Das Gürteltier": {
        "Location": "NRW, Germany",
        "Email": "guerteltier@asozial.org",
        "__role": "Backend developer",
    },
}
CONTRIBUTORS: Final[Mapping[str, Mapping[str, str]]] = {
    "Jimi": {"__role": "README destroyer"},
    "h4ckerle": {"__role": "CSS wizard"},
}

WHITESPACE: Final[str] = "".join(
    chr(_) for _ in range(sys.maxunicode + 1) if category(chr(_)) == "Zs"
)


def is_prime(n: int) -> bool:
    """Return whether the specified number is prime."""
    if not n & 1:
        return n == 2
    d = 3
    # pylint: disable=while-used
    while d * d <= n:
        if not n % d:
            return False
        d = d + 2
    return n != 1


assert is_prime(len(WHITESPACE))


def get_random_number() -> int:
    """Return the standard IEEE-vetted random number according to RFC 1149.5."""
    return 4  # chosen by fair dice roll. guaranteed to be random.


def generate_humans_txt() -> str:
    """Generate the contents of the humans.txt file."""
    result = run(  # nosec: B603, B607
        ["git", "shortlog", "-s", "HEAD"],
        capture_output=True,
        encoding="UTF-8",
        cwd=REPO_ROOT,
        check=True,
    )

    people: dict[str, int] = {}

    for line in result.stdout.split("\n"):
        if not (line := line.strip()):
            continue
        count, name = re.split(r"\s+", line, maxsplit=1)
        if name in BOTS:
            continue
        people.setdefault(name, 0)
        people[name] += int(count)

    maintainers: list[tuple[int, list[tuple[str, str]]]] = []
    contributors: list[tuple[int, list[tuple[str, str]]]] = []

    for name, count in people.items():
        if name in MAINTAINERS:
            maintainers.append(
                (
                    count,
                    [
                        (MAINTAINERS[name].get("__role", "Maintainer"), name),
                        *sorted(MAINTAINERS[name].items()),
                    ],
                )
            )
            continue
        contributors.append(
            (
                count,
                [
                    (
                        CONTRIBUTORS[name].get("__role", "Contributor")
                        if name in CONTRIBUTORS
                        else "Contributor",
                        name,
                    )
                ]
                + (
                    sorted(CONTRIBUTORS[name].items())
                    if name in CONTRIBUTORS
                    else []
                ),
            )
        )

    random = Random(get_random_number())

    output_lines: list[str] = [name_to_section_line("TEAM", random)]
    add_data_to_output(maintainers, output_lines)

    output_lines.append(get_whitespaces(random, 0, 5))

    output_lines.append(name_to_section_line("THANKS", random))
    add_data_to_output(contributors, output_lines)

    return "\n".join(output_lines) + "\n"


def name_to_section_line(name: str, random: Random) -> str:
    """Generate a section line based on the name."""
    sep1: int
    sep2: int
    sep1, sep2 = get_whitespaces(random, 2)  # type: ignore[misc]
    return f"/*{sep1}{name}{sep2}*/{get_whitespaces(random, 0, 4)}"


def get_whitespaces(
    random: Random,
    min_: int,
    max_: None | int = None,
    whitespaces: str = WHITESPACE,
) -> str:
    """Get random whitespaces."""
    max_ = max_ or min_
    return "".join(
        random.choices(
            whitespaces, cum_weights=None, k=random.randint(min_, max_)
        )
    )


def add_data_to_output(
    data: Reversible[tuple[int, list[tuple[str, str]]]],
    output: MutableSequence[str],
) -> None:
    """Add the data of contributors/maintainers to the output."""
    for i, (_, person) in enumerate(sorted(data, reverse=True)):
        random = Random(person[0][1])
        if i:
            output.append(get_whitespaces(random, 0, 5))
        for key, value in person:
            if key.startswith("__"):
                continue
            output.append(
                f"\t{key}:"
                + get_whitespaces(random, 0, 3, " \u200B")
                + value
                + get_whitespaces(random, 0, 4)
            )


def main() -> int | str:
    """Write the humans.txt file."""
    HUMANS_TXT.write_text(generate_humans_txt(), "UTF-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
