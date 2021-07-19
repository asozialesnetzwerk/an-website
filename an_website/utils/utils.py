from __future__ import annotations, barry_as_FLUFL

import asyncio
import asyncio.subprocess
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

from ansi2html import Ansi2HTMLConverter  # type: ignore
from tornado.web import HTTPError, RequestHandler

Handler = Union[
    Tuple[str, Any],
    Tuple[str, Any, Dict[str, Any]],
    Tuple[str, Any, Dict[str, Any], str],
]
HandlerList = Tuple[Handler, ...]


@dataclass()
class PageInfo:
    name: str
    description: str
    path: Optional[str] = None


@dataclass()
class ModuleInfo(PageInfo):
    handlers: HandlerList = field(default_factory=HandlerList)
    sub_pages: Optional[Tuple[PageInfo, ...]] = None


def get_module_info() -> ModuleInfo:
    return ModuleInfo(
        "Utilitys",
        "Nütliche Werkzeuge für alle möglichen Sachen.",
        handlers=((r"/error/?", ZeroDivision),),
    )


def length_of_match(_m: re.Match):
    span = _m.span()
    return span[1] - span[0]


def n_from_set(_set: set, _n: int) -> set:
    i = 0
    new_set = set()
    for _el in _set:
        if i < _n:
            i += 1
            new_set.add(_el)
        else:
            break
    return new_set


def strtobool(val):
    """Convert a string representation of truth to True or False."""
    val = val.lower()
    if val in ("sure", "y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("nope", "n", "no", "f", "false", "off", "0"):
        return False
    raise ValueError("invalid truth value %r" % (val,))


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
    RATELIMIT_TOKENS = 1  # can be overridden in subclasses
    header_text = "Das Asoziale Netzwerk"

    def initialize(self, **kwargs):
        header_text = kwargs.get("header_text", None)
        if header_text is not None:
            self.header_text = header_text

    def data_received(self, chunk):
        pass

    async def prepare(self):  # pylint: disable=invalid-overridden-method
        if not sys.flags.dev_mode and not self.request.method == "OPTIONS":
            now = datetime.utcnow()
            redis = self.settings.get("REDIS")
            prefix = self.settings.get("REDIS_PREFIX")
            tokens = getattr(
                self, "RATELIMIT_TOKENS_" + self.request.method, None
            )
            if tokens is None:
                tokens = self.RATELIMIT_TOKENS
            result = await redis.execute_command(
                "CL.THROTTLE",
                prefix + "ratelimit:" + self.request.remote_ip,
                15,  # max burst
                30,  # count per period
                60,  # period
                tokens,
            )
            self.set_header("X-RateLimit-Limit", result[1])
            self.set_header("X-RateLimit-Remaining", result[2])
            self.set_header("Retry-After", result[3])
            self.set_header("X-RateLimit-Reset", result[4])
            if result[0]:
                if now.month == 4 and now.day == 20:
                    self.set_status(420, "Enhance Your Calm")
                    self.write_error(420)
                else:
                    self.set_status(429)
                    self.write_error(429)

    def write_error(self, status_code, **kwargs):
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
        )

    def get_error_message(self, **kwargs):
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][:2])[-1]
        return self._reason

    def get_template_namespace(self):
        namespace = super().get_template_namespace()
        no_js: bool = self.get_query_argument_as_bool("no_js", False)
        form_appendix: str = (
            "<input name='no_js' style='display: none;"
            + "width: 0; height: 0; opacity: 0' value='sure'>"
            if no_js
            else ""
        )
        namespace.update(
            {
                "ansi2html": Ansi2HTMLConverter(inline=True, scheme="xterm"),
                "header_text": self.header_text,
                "no_js": no_js,
                "url_appendix": "?no_js=sure" if no_js else "",
                "form_appendix": form_appendix,
                # this is not important because we don't need the templates
                # in a context without the request for soundboard and wiki
                "url": self.request.full_url(),
                "settings": self.settings,
            }
        )
        return namespace

    def get_query_argument_as_bool(self, name: str, default: bool = False):
        return strtobool(
            str(self.get_query_argument(name, default=str(default)))
        )


class APIRequestHandler(BaseRequestHandler):
    def write_error(self, status_code, **kwargs):
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    RATELIMIT_TOKENS = 0

    async def prepare(self):
        raise HTTPError(404)


class ZeroDivision(BaseRequestHandler):
    RATELIMIT_TOKENS = 10

    async def prepare(self):
        if not self.request.method == "OPTIONS":
            await super().prepare()
            self.finish(str(0 / 0))
