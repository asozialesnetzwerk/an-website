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

import re
from typing import Optional, Union

from tornado.web import RequestHandler

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


def string_to_num(string: str, divide_by: int = 1) -> Optional[float]:
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


async def conversion_string(value_dict: dict) -> str:
    """Generate a text that complains how expensive everything is."""
    return (
        f"{value_dict.get('euro_str')} Euro, "
        f"das sind ja {value_dict.get('mark_str')} Mark; "
        f"{value_dict.get('ost_str')} Ostmark "
        f"und {value_dict.get('schwarz_str')} Ostmark auf dem Schwarzmarkt!"
    )


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
ValueDict = dict[str, Union[str, float, bool]]


async def get_value_dict(euro: float) -> ValueDict:
    """Create the value dict base on the euro."""
    value_dict: dict[str, Union[str, float]] = {}
    for _i, key in enumerate(keys):
        val = multipliers[_i] * euro
        value_dict[key] = val
        value_dict[key + "_str"] = num_to_string(val)

    value_dict["text"] = await conversion_string(value_dict)

    return value_dict


async def arguments_to_value_dict(
    request_handler: RequestHandler,
) -> Optional[ValueDict]:
    """
    Parse the arguments to get the value dict and return it.

    Return None if no argument is given.
    """
    arg_list: list[tuple[int, str, str]] = []

    for _i, key in enumerate(keys):
        num_str = request_handler.get_query_argument(name=key, default=None)
        if num_str is not None:
            arg_list.append((_i, key, num_str))

    print(arg_list)

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


class CurrencyConverter(BaseRequestHandler):
    """Request handler for the currency converter page."""

    async def get(self):
        """Handle the GET request and display the page."""
        value_dict = await arguments_to_value_dict(self)
        if value_dict is None:
            value_dict = await get_value_dict(0)
            description = self.description
        else:
            description = value_dict["text"]

        replace_url_with = None

        if value_dict.get("too_many_params", False):
            key = value_dict.get("key_used")
            replace_url_with = self.fix_url(
                f"{self.request.path}?{key}={value_dict.get(key + '_str')}"
            )

        await self.render(
            "pages/converter.html",
            **value_dict,
            description=description,
            replace_url_with=replace_url_with,
        )


class CurrencyConverterAPI(APIRequestHandler):
    """Request handler for the currency converter JSON API."""

    async def get(self):
        """
        Handle the GET request and return the value dict as JSON.

        If no arguments are given the potential arguments are shown.
        """
        value_dict = await arguments_to_value_dict(self)
        if value_dict is None:
            await self.finish(dict(zip(keys, [None] * len(keys))))
            return

        await self.finish(value_dict)
