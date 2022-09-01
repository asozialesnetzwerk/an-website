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

"""A page that converts german currencies."""

from __future__ import annotations

import random
from typing import cast

import regex

from ..utils.request_handler import APIRequestHandler, HTMLRequestHandler
from ..utils.utils import ModuleInfo

KEYS = ("euro", "mark", "ost", "schwarz")
MULTIPLIERS = (1, 2, 4, 20)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/waehrungs-rechner", CurrencyConverter),
            (r"/api/waehrungs-rechner", CurrencyConverterAPI),
        ),
        name="Währungsrechner",
        description=(
            "Ein Währungsrechner für teilweise veraltete deutsche Währungen"
        ),
        path="/waehrungs-rechner",
        keywords=(
            "Währungsrechner",
            "converter",
            "Euro",
            "D-Mark",
            "Ost-Mark",
            "Känguru",
        ),
        aliases=(
            "/rechner",
            "/w%C3%A4hrungs-rechner",
            "/währungs-rechner",
            "/currency-converter",
        ),
    )


def string_to_num(num: str, divide_by: int = 1) -> int:
    """Convert a string to a number and divide it by divide_by."""
    num = regex.sub(r"[^\d,]", "", num.replace(".", ","))

    if not num:
        return 0

    if "," not in num:
        return (int(num) * 100) // divide_by

    split = [spam for spam in num.split(",") if spam]
    if not split:
        return 0

    if len(split) == 1:
        return (int(split[0]) * 100) // divide_by

    dec = split[-1]
    pre = "".join(split[:-1])

    return (int(pre or "0") * 100 + int((dec + "00")[0:2])) // divide_by


def num_to_string(num: int) -> str:
    """
    Convert a float to the german representation of a number.

    The number has 2 or 0 digits after the comma.
    """
    if not num:
        return "0"
    string = f"00{num}"
    string = (string[0:-2].lstrip("0") or "0") + "," + string[-2:]
    return string.removesuffix(",00")


async def conversion_string(value_dict: ValueDict) -> str:
    """Generate a text that complains how expensive everything is."""
    return (
        f"{value_dict.get('euro_str')} Euro, "
        f"das sind ja {value_dict.get('mark_str')} Mark; "
        f"{value_dict.get('ost_str')} Ostmark und "
        f"{value_dict.get('schwarz_str')} Ostmark auf dem Schwarzmarkt!"
    )


async def continuation_string(
    values: ValuesTuple,
    ticket_price: None | int = None,
    ins_kino_gehen: None | str = None,
) -> str:
    """Generate a second text that complains how expensive everything is."""
    price: int = ticket_price or values[0]
    if not ins_kino_gehen:
        ins_kino_gehen = "ins Kino gehen"
    price_ostmark: int = (
        100
        if ins_kino_gehen == "ins Kino gehen"
        else int(max(round(price // 8) // 2, 50))
    )
    _rand = random.Random(f"{price}|{values}|{ins_kino_gehen}")
    kino_count: int = values[-1] // price_ostmark
    output = [
        "Und ich weiß nicht, ob ihr das noch wisst, aber man konnte locker für",
        "eine" if price_ostmark == 100 else num_to_string(price_ostmark),
        (
            f"Ostmark {ins_kino_gehen}! Das heißt man konnte von "
            f"{num_to_string(values[-1])} Ostmark "
            f"{kino_count}-mal {ins_kino_gehen}."
        ),
    ]
    while True:  # pylint: disable=while-used
        euro, mark, ost, schwarz = convert(int(price * kino_count))
        no_time = (
            " — dafür habt ihr ja keine Zeit im Kapitalismus, "
            "aber wenn ihr die Zeit hättet —"
            if mark > 20_300_000_000 * 100
            else ""
        )
        output.append(
            f"Wenn ihr aber heute {kino_count}-mal "
            f"{ins_kino_gehen} wollt{no_time}, müsst ihr"
        )
        if euro > 1_000_000 * 100:
            output.append("...äh...")
        output.append(f"{num_to_string(euro)} Euro bezahlen.")
        output.append(
            _rand.choice(
                (
                    "Ja! Ja! Ich weiß, was ihr denkt!",
                    "Ja, ja, ich weiß, was ihr denkt!",
                    "Ich weiß, was ihr denkt!",
                )
            )
        )
        if mark > 20_300_000_000 * 100:  # Staatsschulden der DDR
            output.append(  # the end of the text
                "Davon hätte man die DDR entschulden können! "
                f"Von einmal {ins_kino_gehen}. "
                "So teuer ist das alles geworden."
            )
            break
        new_kino_count = int((schwarz * price_ostmark) // 100)
        # TODO: add random chance to get approximation
        output.append(
            f"{num_to_string(mark)} Mark, {num_to_string(ost)} Ostmark, "
            f"{num_to_string(schwarz)} Ostmark auf dem Schwarzmarkt, "
            f"davon konnte man {new_kino_count}-mal {ins_kino_gehen}."
        )
        if new_kino_count <= kino_count:
            # it doesn't grow, exit to avoid infinite loop
            break
        kino_count = new_kino_count

    return " ".join(output)


ValueDict = dict[str, str | int | bool]
ValuesTuple = tuple[int, int, int, int]


def convert(euro: int) -> ValuesTuple:
    """Convert a number to the german representation of a number."""
    return cast(ValuesTuple, tuple(euro * _m for _m in MULTIPLIERS))


async def get_value_dict(
    euro: int,
    ins_kino_gehen: None | str = None,
) -> ValueDict:
    """Create the value dict base on the euro."""
    values = convert(euro)
    value_dict: ValueDict = {}
    for key, val in zip(KEYS, values):
        value_dict[key] = val
        value_dict[key + "_str"] = num_to_string(val)

    value_dict["text"] = await conversion_string(value_dict)
    value_dict["text2"] = await continuation_string(
        values, ins_kino_gehen=ins_kino_gehen
    )
    return value_dict


class CurrencyConverter(HTMLRequestHandler):
    """Request handler for the currency converter page."""

    async def create_value_dict(self) -> None | ValueDict:
        """
        Parse the arguments to get the value dict and return it.

        Return None if no argument is given.
        """
        arg_list: list[tuple[int, str, str]] = []

        for i, key in enumerate(KEYS):
            num_str = self.get_argument(key, None)
            if num_str is not None:
                arg_list.append((i, key, num_str))

        too_many_params = len(arg_list) > 1

        for i, key, num_str in arg_list:
            euro = string_to_num(num_str, MULTIPLIERS[i])
            if euro is not None:
                value_dict: ValueDict = await get_value_dict(
                    euro, ins_kino_gehen=self.get_argument("text", None)
                )
                if too_many_params:
                    value_dict["too_many_params"] = True
                value_dict["key_used"] = key
                return value_dict

        return None

    async def get(self, *, head: bool = False) -> None:
        """Handle GET requests to the currency converter page."""
        value_dict = await self.create_value_dict()
        if value_dict is None:
            value_dict = await get_value_dict(0)
            description = self.description
        else:
            description = cast(str, value_dict["text"])

        if head:
            return

        if value_dict.get("too_many_params", False):
            used_key = value_dict.get("key_used")
            replace_url_with = self.fix_url(
                self.request.full_url(),
                **{  # type: ignore[arg-type]
                    key: value_dict.get(f"{used_key}_str")
                    if key == used_key
                    else None
                    for key in KEYS
                },
            )
            if replace_url_with != self.request.full_url():
                return self.redirect(replace_url_with)

        await self.render(
            "pages/converter.html",
            **value_dict,
            description=description,
        )


class CurrencyConverterAPI(APIRequestHandler, CurrencyConverter):
    """Request handler for the currency converter API."""

    async def get(self, *, head: bool = False) -> None:
        """
        Handle GET requests to the currency converter API.

        If no arguments are given the potential arguments are shown.
        """
        value_dict = await self.create_value_dict()

        if head:
            return

        if value_dict is None:
            return await self.finish(dict(zip(KEYS, [None] * len(KEYS))))

        for key in KEYS:
            value_dict[key] = value_dict.pop(f"{key}_str")

        return await self.finish(value_dict)
