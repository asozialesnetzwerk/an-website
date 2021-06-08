from typing import Optional, Awaitable

from tornado import template
from tornado import web
import json
import re

from utils.utils import get_url

keys = ["euro", "mark", "ost", "schwarz"]
multipliers = [1, 2, 4, 20]


def string_to_num(string, divide_by=1):
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


def num_to_string(num):
    return f"{num:.2f}".replace(".", ",").replace(",00", "")


def conversion_string(value_dict):
    return f"{value_dict.get('euro_str')} Euro, " \
           f"das sind ja {value_dict.get('mark_str')} Mark; " \
           f"{value_dict.get('ost_str')} Ostmark " \
           f"und {value_dict.get('schwarz_str')} Ostmark auf dem Schwarzmarkt!"


def get_value_dict(euro):
    value_dict = {}

    for i in range(len(keys)):
        val = multipliers[i] * euro
        value_dict[keys[i]] = val
        value_dict[keys[i] + "_str"] = num_to_string(val)

    value_dict["text"] = conversion_string(value_dict)

    return value_dict


def arguments_to_value_dict(request_handler):
    for i in range(len(keys)):
        num_str = request_handler.get_query_argument(name=keys[i], default=None)
        euro = string_to_num(num_str, multipliers[i])
        if euro is not None:
            return get_value_dict(euro)


class CurrencyConverter(web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self, arg2):
        value_dict = arguments_to_value_dict(self)
        if value_dict is None:
            value_dict = get_value_dict(16)

        value_dict["url"] = get_url(self)  # dirty fix, please remove

        loader = template.Loader("")
        html = loader.load(name="currency_converter/converter.html")
        self.add_header("Content-Type", "text/html; charset=UTF-8")
        self.write(html.generate(**value_dict))


class CurrencyConverterApi(web.RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self, arg2):
        value_dict = arguments_to_value_dict(self)
        if value_dict is None:
            self.write("Arguments: " + str(keys))
            return

        self.add_header("Content-Type", "application/json")
        self.write(json.dumps(value_dict))
