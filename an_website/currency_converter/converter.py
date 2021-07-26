from __future__ import annotations, barry_as_FLUFL

import re
from typing import Optional

from tornado.web import RequestHandler

from ..utils.utils import APIRequestHandler, BaseRequestHandler, ModuleInfo

keys = ["euro", "mark", "ost", "schwarz"]
multipliers = [1, 2, 4, 20]


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        handlers=(
            (r"/(w(ae|%C3%A4|ä)hrungs-)?rechner/?", CurrencyConverter),
            (r"/(w(ae|%C3%A4|ä)hrungs-)?rechner/api/?", CurrencyConverterAPI),
        ),
        name="Währungsrechner",
        description="Ein Währungsrechner für teilweise veraltete deutsche "
        "Währungen",
        path="/waehrungs-rechner",
    )


async def string_to_num(string: str, divide_by: int = 1) -> Optional[float]:
    if string is None or len(string) == 0:
        return None

    string = string.replace(",", ".")
    try:
        return float(string) / divide_by
    except ValueError:
        try:
            return float(re.sub(r"[^0-9\.]", "", string)) / divide_by
        except ValueError:
            return None


async def num_to_string(num: float) -> str:
    return f"{num:.2f}".replace(".", ",").replace(",00", "")


async def conversion_string(value_dict: dict) -> str:
    return (
        f"{value_dict.get('euro_str')} Euro, "
        f"das sind ja {value_dict.get('mark_str')} Mark; "
        f"{value_dict.get('ost_str')} Ostmark "
        f"und {value_dict.get('schwarz_str')} Ostmark auf dem Schwarzmarkt!"
    )


async def get_value_dict(euro):
    # TypedDict('value_dict', {"euro": float, "mark": float, "ost": float, "schwarz": float,  # noqa
    # "euro_str": str, "mark_str": str, "ost_str": str, "schwarz_str": str, "text": str})  # noqa
    value_dict = {}

    for _i, key in enumerate(keys):
        val = multipliers[_i] * euro
        value_dict[key] = val
        value_dict[key + "_str"] = await num_to_string(val)

    value_dict["text"] = await conversion_string(value_dict)

    return value_dict


async def arguments_to_value_dict(
    request_handler: RequestHandler,
) -> Optional[dict]:
    arg_list: list[tuple[int, str, str]] = []

    for _i, key in enumerate(keys):
        num_str = request_handler.get_query_argument(name=key, default=None)
        if num_str is not None:
            arg_list.append((_i, key, num_str))

    print(arg_list)

    too_many_params: bool = len(arg_list) > 1

    for _i, key, num_str in arg_list:
        euro = await string_to_num(num_str, multipliers[_i])

        if euro is not None:
            value_dict = await get_value_dict(euro)

            if too_many_params:
                value_dict["too_many_params"] = True

            value_dict["key_used"] = key

            return value_dict
    return None


class CurrencyConverter(BaseRequestHandler):
    async def get(self, *args):  # pylint: disable=unused-argument
        value_dict = await arguments_to_value_dict(self)
        if value_dict is None:
            value_dict = await get_value_dict(0)
            description = self.description
        else:
            description = value_dict["text"]

        if value_dict.get("too_many_params", False):
            url = self.request.full_url().split("?")[0]
            key = value_dict.get("key_used")
            redirect_url = f"{url}?{key}={value_dict.get(key + '_str')}"
            if self.get_no_3rd_party():
                redirect_url += "&no_3rd_party=sure"
            self.redirect(redirect_url)
            return

        await self.render(
            "pages/converter.html", **value_dict, description=description
        )


class CurrencyConverterAPI(APIRequestHandler):
    async def get(self, *args):  # pylint: disable=unused-argument
        value_dict = await arguments_to_value_dict(self)
        if value_dict is None:
            self.write("Arguments: " + str(keys))
            return

        self.write(value_dict)
