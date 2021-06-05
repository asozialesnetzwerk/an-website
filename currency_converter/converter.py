import web

keys = ["euro", "mark", "ost", "schwarz"]
multipliers = [1, 2, 4, 20]


def string_to_num(string, divide_by=1):
    if string is None:
        return None
    return float(string.replace(",", ".")) / divide_by


def num_to_string(num):
    return f"{num:.2f}".replace(".", ",").replace(",00", "")


def conversion_string(euro):
    return f"{num_to_string(euro)} Euro, " \
           f"das sind ja {num_to_string(euro * 2)} Mark; " \
           f"{num_to_string(euro * 4)} Ostmark " \
           f"und {num_to_string(euro * 20)} Ostmark auf dem Schwarzmarkt! "


def get_value_dict(euro):
    value_dict = {}

    for i in range(len(keys)):
        value_dict[keys[i]] = multipliers[i] * euro

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

        value_dict["url"] = web.ctx.home + web.ctx.path + web.ctx.query
        print(value_dict)
        html = web.template.frender("currency_converter/index.html", globals=value_dict)
        return html()


class CurrencyConverterApi:
    def GET(self, test):
        value_dict = arguments_to_value_dict(web.input())
        if value_dict is None:
            return "Arguments: " + str(keys)
        return str(value_dict)
