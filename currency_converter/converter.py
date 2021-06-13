from __future__ import annotations
import re

from utils.utils import get_url, RequestHandlerCustomError, RequestHandlerJsonAPI

keys = ["euro", "mark", "ost", "schwarz"]
multipliers = [1, 2, 4, 20]


async def string_to_num(string: str, divide_by: int = 1) -> Optional[float]:
    if string is None or len(string) is 0:
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
    return f"{value_dict.get('euro_str')} Euro, " \
           f"das sind ja {value_dict.get('mark_str')} Mark; " \
           f"{value_dict.get('ost_str')} Ostmark " \
           f"und {value_dict.get('schwarz_str')} Ostmark auf dem Schwarzmarkt!"


async def get_value_dict(euro: float) -> dict:
    value_dict = {}

    for i in range(len(keys)):
        val = multipliers[i] * euro
        value_dict[keys[i]] = val
        value_dict[keys[i] + "_str"] = await num_to_string(val)

    value_dict["text"] = await conversion_string(value_dict)

    return value_dict


async def arguments_to_value_dict(request_handler):
    contains_bad_param = False
    for i in range(len(keys)):
        num_str = request_handler.get_query_argument(name=keys[i], default=None)
        if num_str is not None:
            euro = await string_to_num(num_str, multipliers[i])
            if euro is not None:
                value_dict = await get_value_dict(euro)
                if contains_bad_param:
                    value_dict["contained_bad_param"] = True
                value_dict["key_used"] = keys[i]
                return value_dict
            else:
                contains_bad_param = True


class CurrencyConverter(RequestHandlerCustomError):
    async def get(self, *args):
        value_dict = await arguments_to_value_dict(self)
        if value_dict is None:
            value_dict = await get_value_dict(16)

        if value_dict.get("contained_bad_param", False):
            url = get_url(self).split("?")[0]
            key = value_dict.get("key_used")
            self.redirect(f"{url}?{key}={value_dict.get(key + '_str')}")
            return

        #self.add_header("Content-Type", "text/html; charset=UTF-8")
        await self.render("pages/converter.html", **value_dict)


class CurrencyConverterAPI(RequestHandlerJsonAPI):
    async def get(self, *args):
        value_dict = await arguments_to_value_dict(self)
        if value_dict is None:
            self.write("Arguments: " + str(keys))
            return

        self.write(value_dict)
