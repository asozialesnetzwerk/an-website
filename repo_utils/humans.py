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

"""Generates a humans.txt file."""

from __future__ import annotations

import re
from os.path import abspath, dirname
from pathlib import Path
from subprocess import run

REPO_ROOT = dirname(dirname(abspath(__file__)))
HUMANS_TXT = Path(REPO_ROOT, "an_website/static/humans.txt")

# edit these 3 to change humans.txt
BOTS: set[str] = {"ImgBotApp", "snyk-bot"}
NAME_ALIASES: dict[str, str] = {
    "Joshix-1": "Joshix",
    "Guerteltier": "Das Gürteltier",
}
MAINTAINERS: dict[str, dict[str, str]] = {
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
CONTRIBUTORS: dict[str, dict[str, str]] = {
    "Jimi": {"__role": "README destroyer"},
    "h4ckerle": {"__role": "CSS wizard"},
}


def generate_humans_txt() -> str:
    """Generate the contents of the humans.txt file."""
    result = run(
        ["git", "shortlog", "-s", "HEAD"], capture_output=True, check=True
    )

    people: dict[str, int] = {}

    for line in result.stdout.decode("utf-8").split("\n"):
        if not line.strip():
            continue
        count, name = re.split(r"\s+", line.strip(), 1)
        if name in BOTS:
            continue
        name = NAME_ALIASES.get(name, name)
        if name in people:
            people[name] += int(count)
        else:
            people[name] = int(count)

    maintainers: list[tuple[int, list[tuple[str, str]]]] = []
    contributors: list[tuple[int, list[tuple[str, str]]]] = []

    for name, count in people.items():
        if name in MAINTAINERS:
            maintainers.append(
                (
                    count,
                    [
                        (MAINTAINERS[name].get("__role", "Maintainer"), name),
                        *sorted(list(MAINTAINERS[name].items())),
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

    output_lines: list[str] = ["/* TEAM */"]
    add_data_to_output(maintainers, output_lines)
    # print("Maintainers:\t", [person[0][1] for _, person in maintainers])

    output_lines.append("/* THANKS */")
    add_data_to_output(contributors, output_lines)
    # print("Contributors:\t", [person[0][1] for _, person in contributors])

    return "\n".join(output_lines).strip() + "\n"


def add_data_to_output(
    data: list[tuple[int, list[tuple[str, str]]]], output: list[str]
) -> None:
    """Add the data of contributors/maintainers to the output."""
    for _, person in sorted(data, reverse=True):
        for key, value in person:
            if key.startswith("__"):
                continue
            output.append(f"\t{key}: {value}")
        output.append("")


if __name__ == "__main__":
    HUMANS_TXT.write_text(generate_humans_txt(), "utf-8")
