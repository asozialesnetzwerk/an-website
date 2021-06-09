import os
from typing import Optional, Awaitable, Any

from tornado.web import RequestHandler


def get_url(request_handler):
    return request_handler.request.full_url() \
        .replace("http://j", "https://j")  # Dirty fix to force https


# Uses sha1sum to keep it the same
def hash_string(string):
    string = string.strip().replace('"', '\\"')
    res = os.popen(f"echo \"{string}\" | sha1sum | cut -d ' ' -f 1")
    return res.read()


class RequestHandlerCustomError(RequestHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        self.render("error.html", error_code=status_code, url=get_url(self))
