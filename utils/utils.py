import os


def get_url(request_handler):
    return request_handler.request.full_url() \
        .replace("http://j", "https://j")


# Uses sha256sum to keep it the same
def hash_string(string):
    string = string.strip().replace('"', '\\"')
    res = os.popen(f"echo \"{string}\" | sha256sum | cut -d ' ' -f 1")
    return res.read()
