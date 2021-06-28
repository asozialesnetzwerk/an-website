from __future__ import annotations, barry_as_FLUFL

import asyncio
import asyncio.subprocess
import re
import traceback
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

from tornado.web import HTTPError, RequestHandler

Handler = Union[
    Tuple[str, Any],
    Tuple[str, Any, Dict[str, Any]],
    Tuple[str, Any, Dict[str, Any], str],
]
HandlerList = Tuple[Handler, ...]


@dataclass()
class ModuleInfo:
    handlers: HandlerList
    name: str = "name"
    description: str = "description"
    path: Optional[str] = None


def get_module_info() -> ModuleInfo:
    return ModuleInfo(handlers=((r"/error/?", ZeroDivision),))


def length_of_match(m: re.Match):  # pylint: disable=invalid-name
    span = m.span()
    return span[1] - span[0]


async def run(cmd, stdin=asyncio.subprocess.PIPE):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=stdin,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


class BaseRequestHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def write_error(self, status_code, **kwargs):
        self.render(
            "error.html",
            code=status_code,
            message=self.get_error_message(**kwargs),
        )

    def get_error_message(self, **kwargs):
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][:2])[-1]
        return self._reason


class APIRequestHandler(BaseRequestHandler):
    def write_error(self, status_code, **kwargs):
        self.write(
            {
                "status": status_code,
                "message": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    def prepare(self):
        raise HTTPError(404)


class ZeroDivision(BaseRequestHandler):
    def get(self):
        self.finish(str(0 / 0))
