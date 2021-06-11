import os
import traceback

from tornado.web import RequestHandler, HTTPError


def get_url(request_handler):
    "Dirty fix to force https"
    return request_handler.request.full_url() \
        .replace("http://", "https://")

def hash_string(string):
    "Uses sha1sum to keep it the same"
    string = string.strip().replace('"', '\\"')
    res = os.popen(f"echo \"{string}\" | sha1sum | cut -d ' ' -f 1")
    return res.read()

class RequestHandlerCustomError(RequestHandler):
    def write_error(self, status_code, **kwargs):
        if "exc_info" in kwargs and not issubclass(kwargs["exc_info"][0], HTTPError):
            if self.settings.get("serve_traceback"):
                message = ''.join(traceback.format_exception(*kwargs["exc_info"]))
            else:
                message = traceback.format_exception_only(*kwargs["exc_info"][0:2])[-1]
        else:
            message = self._reason
        self.render("error.html", url=get_url(self), code=status_code, message=message)

class RequestHandlerNotFound(RequestHandlerCustomError):
    #def options(self): self.set_status(404)
    #def head(self): self.set_status(404)
    #def get(self): self.write_error(404)
    #def post(self): self.write_error(404)
    #def delete(self): self.write_error(404)
    #def patch(self): self.write_error(404)
    #def put(self): self.write_error(404)
    def prepare(self):
        raise HTTPError(404)

class RequestHandlerDivideByZero(RequestHandlerCustomError):
    def get(self):
        0/0
