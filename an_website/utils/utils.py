import asyncio
import asyncio.subprocess
import re
import traceback
from typing import Awaitable, Optional

from tornado.web import HTTPError, RequestHandler, StaticFileHandler


def get_handlers() -> tuple:
    return r"/error/?", RequestHandlerZeroDivision


def length_of_match(m: re.Match):  # pylint: disable=invalid-name
    span = m.span()
    return span[1] - span[0]


def get_url(request_handler: RequestHandler):
    """Dirty fix to force https"""
    return request_handler.request.full_url().replace("http://j", "https://j")


async def run_shell(cmd, stdin=asyncio.subprocess.PIPE):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdin=stdin, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


async def run_exec(cmd, stdin=asyncio.subprocess.PIPE):
    proc = await asyncio.create_subprocess_exec(
        cmd, stdin=stdin, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


class RequestHandlerBase(RequestHandler):
    def data_received(self, chunk):
        pass

    def render(self, template_name, **kwargs):
        return super().render(template_name, **kwargs, url=get_url(self))

    def get_error_message(self, **kwargs):
        if "exc_info" in kwargs and not issubclass(kwargs["exc_info"][0], HTTPError):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][0:2])[-1]
        return self._reason



class RequestHandlerCustomError(RequestHandlerBase):
    def write_error(self, status_code, **kwargs):
        self.render(
            "error.html", code=status_code, message=self.get_error_message(**kwargs)
        )


class RequestHandlerJsonAPI(RequestHandlerBase):
    def write_error(self, status_code, **kwargs):
        self.write({"status": status_code, "message": self.get_error_message(**kwargs)})


class RequestHandlerNotFound(RequestHandlerCustomError):
    # def options(self): self.set_status(404)
    # def head(self): self.set_status(404)
    # def get(self): self.write_error(404)
    # def post(self): self.write_error(404)
    # def delete(self): self.write_error(404)
    # def patch(self): self.write_error(404)
    # def put(self): self.write_error(404)
    def prepare(self):
        raise HTTPError(404)


class RequestHandlerZeroDivision(RequestHandlerCustomError):
    def get(self):
        0 / 0  # pylint: disable=pointless-statement
