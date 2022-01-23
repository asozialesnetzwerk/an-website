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

"""The currency converter page that converts german currencies."""
from __future__ import annotations

import random
import re

from ..utils.request_handler import APIRequestHandler, BaseRequestHandler
from ..utils.utils import ModuleInfo

keys = ["euro", "mark", "ost", "schwarz"]
multipliers = [1, 2, 4, 20]


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=(
            (r"/waehrungs-rechner/", CurrencyConverter),
            (r"/api/waehrungs-rechner/", CurrencyConverterAPI),
        ),
        name="Währungsrechner",
        description="Ein Währungsrechner für teilweise veraltete deutsche "
        "Währungen",
        path="/waehrungs-rechner/",
        keywords=(
            "Währungsrechner",
            "converter",
            "Euro",
            "D-Mark",
            "Ost-Mark",
            "Känguru",
        ),
        aliases=(
            "/rechner/",
            "/w%C3%A4hrungs-rechner/",
            "/währungs-rechner/",
            "/currency-converter/",
        ),
    )


def string_to_num(string: str, divide_by: int = 1) -> None | float:
    """Convert a string to a number and divide it by divide_by."""
    if not string:
        return None

    string = string.replace(",", ".")
    try:
        return float(string) / divide_by
    except ValueError:
        try:
            return float(re.sub(r"[^0-9\.]", str(), string)) / divide_by
        except ValueError:
            return None


def num_to_string(num: float) -> str:
    """
    Convert a float to the german representation of a number.

    The number has 2 or 0 digits after the comma.
    """
    return f"{num:.2f}".replace(".", ",").replace(",00", str())


async def conversion_string(value_dict: ValueDict) -> str:
    """Generate a text that complains how expensive everything is."""
    return (
        f"{value_dict.get('euro_str')} Euro, "
        f"das sind ja {value_dict.get('mark_str')} Mark; "
        f"{value_dict.get('ost_str')} Ostmark und "
        f"{value_dict.get('schwarz_str')} Ostmark auf dem Schwarzmarkt!"
    )


async def continuation_string(
    values: ValuesTuple, ticket_price: None | float = None
) -> str:
    """Generate a second text that complains how expensive everything is."""
    _ticket_price: float = ticket_price or values[0]
    _rand = random.Random(_ticket_price)
    kino_count = int(values[-1])
    output = [
        "Und ich weiß nicht, ob ihr das noch wisst, aber man konnte locker "
        "für eine Ostmark ins Kino gehen! Das heißt man konnte "
        f"von {values[-1]} Ostmark {kino_count}-mal ins Kino gehen."
    ]
    while True:  # pylint: disable=while-used
        euro, mark, ost, schwarz = convert(_ticket_price * kino_count)
        no_time = (
            (
                " — dafür habt ihr ja keine Zeit im Kapitalismus, "
                "aber wenn ihr die Zeit hättet —"
            )
            if mark > 20_300_000_000
            else str()
        )
        output.append(
            f"Wenn ihr aber heute {kino_count}-mal ins "
            f"Kino gehen wollt{no_time}, müsst ihr heute"
        )
        if euro > 1_000_000:
            output.append("...äh...")
        output.append(f"{num_to_string(euro)} Euro bezahlen.")
        if mark > 20_300_000_000:  # Staatsschulden der DDR
            output.append(  # the end of the text
                "Ich weiß, was ihr denkt! "
                "Davon hätte man die DDR entschulden können! Von einmal ins "
                "Kino gehen. So teuer ist das alles geworden."
            )
            break
        new_kino_count = int(schwarz)
        output.append(
            _rand.choice(
                (
                    "Ja! Ja! Ich weiß, was ihr denkt!",
                    "Ja, ja, ich weiß, was ihr denkt!",
                    "Ich weiß, was ihr denkt!",
                )
            )
        )
        # TODO: Add random chance to get approximation
        output.append(
            f"{num_to_string(mark)} Mark, {num_to_string(ost)} Ostmark, "
            f"{num_to_string(schwarz)} Ostmark auf dem Schwarzmarkt, "
            f"davon konnte man {new_kino_count}-mal ins Kino gehen."
        )
        if new_kino_count <= kino_count:
            # it doesn't grow, exit to avoid infinite loop
            break
        kino_count = new_kino_count

    return " ".join(output)


# class ValueDict(TypedDict):
#     euro: float
#     mark: float
#     ost: float
#     schwarz: float
#     euro_str: str
#     mark_str: str
#     ost_str: str
#     schwarz_str: str
#     text: str
ValueDict = dict[str, str | float | bool]
#                    euro, mark,  ost,   schwarz
ValuesTuple = tuple[float, float, float, float]


def convert(euro: float) -> ValuesTuple:
    """Convert a number to the german representation of a number."""
    return tuple(euro * _m for _m in multipliers)  # type: ignore


async def get_value_dict(euro: float) -> ValueDict:
    """Create the value dict base on the euro."""
    values = convert(euro)
    value_dict: ValueDict = {}
    for key, val in zip(keys, values):
        value_dict[key] = val
        value_dict[key + "_str"] = num_to_string(val)

    value_dict["text"] = await conversion_string(value_dict)
    value_dict["text2"] = await continuation_string(values)
    return value_dict


class CurrencyConverter(BaseRequestHandler):
    """Request handler for the currency converter page."""

    async def get(self) -> None:
        """Handle the GET request and display the page."""
        value_dict = await self.create_value_dict()
        if value_dict is None:
            value_dict = await get_value_dict(0)
            description = self.description
        else:
            description = str(value_dict["text"])

        replace_url_with = None

        if value_dict.get("too_many_params", False):
            key = value_dict.get("key_used")
            replace_url_with = self.fix_url(
                f"{self.request.path}?{key}={value_dict.get(f'{key}_str')}"
            )

        await self.render(
            "pages/converter.html",
            **value_dict,
            description=description,
            replace_url_with=replace_url_with,
        )

    async def create_value_dict(self) -> None | ValueDict:
        """
        Parse the arguments to get the value dict and return it.

        Return None if no argument is given.
        """
        arg_list: list[tuple[int, str, str]] = []

        for _i, key in enumerate(keys):
            num_str = self.get_query_argument(name=key, default=None)
            if num_str is not None:
                arg_list.append((_i, key, num_str))
        # print(arg_list)
        too_many_params: bool = len(arg_list) > 1

        for _i, key, num_str in arg_list:
            euro = string_to_num(num_str, multipliers[_i])

            if euro is not None:
                value_dict: ValueDict = await get_value_dict(euro)

                if too_many_params:
                    value_dict["too_many_params"] = True

                value_dict["key_used"] = key

                return value_dict
        return None


class CurrencyConverterAPI(CurrencyConverter, APIRequestHandler):
    """Request handler for the currency converter JSON API."""

    async def get(self) -> None:
        """
        Handle the GET request and return the value dict as JSON.

        If no arguments are given the potential arguments are shown.
        """
        value_dict = await self.create_value_dict()
        if value_dict is None:
            return await self.finish(dict(zip(keys, [None] * len(keys))))

        return await self.finish(value_dict)
