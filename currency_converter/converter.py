import web
import json

keys = ["euro", "mark", "ost", "schwarz"]
multipliers = [1, 2, 4, 20]


def string_to_num(string, divide_by=1):
    if string is None or len(string) is 0:
        return None
    return float(string.replace(",", ".")) / divide_by


def num_to_string(num):
    return f"{num:.2f}".replace(".", ",").replace(",00", "")


def conversion_string(euro):
    return f"{num_to_string(euro)} Euro, " \
           f"das sind ja {num_to_string(euro * 2)} Mark; " \
           f"{num_to_string(euro * 4)} Ostmark " \
           f"und {num_to_string(euro * 20)} Ostmark auf dem Schwarzmarkt!"


def get_value_dict(euro):
    value_dict = {}

    for i in range(len(keys)):
        val = multipliers[i] * euro
        value_dict[keys[i]] = val
        value_dict[keys[i] + "_str"] = num_to_string(val)

    value_dict["text"] = conversion_string(euro)

    return value_dict


def arguments_to_value_dict(web_input):
    for i in range(len(keys)):
        num_str = web_input.get(keys[i], None)
        euro = string_to_num(num_str, multipliers[i])
        if euro is not None:
            return get_value_dict(euro)


class CurrencyConverter:
    def GET(self, test):
        value_dict = arguments_to_value_dict(web.input())
        if value_dict is None:
            value_dict = get_value_dict(16)

        value_dict["url"] = web.ctx.env.get("wsgi.url_scheme") + "://" \
                            + web.ctx.env.get("HTTP_HOST") \
                            + web.ctx.env.get("PATH_INFO")
        print(value_dict)
        html = web.template.frender("currency_converter/index.html", globals=value_dict)
        web.header("Content-Type", "text/html; charset=UTF-8")
        return html()


class CurrencyConverterApi:
    def GET(self, test):
        value_dict = arguments_to_value_dict(web.input())
        if value_dict is None:
            return "Arguments: " + str(keys)

        web.header('Content-Type', 'application/json')
        return json.dumps(value_dict)
