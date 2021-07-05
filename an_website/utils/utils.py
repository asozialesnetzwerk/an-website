from __future__ import annotations, barry_as_FLUFL

import asyncio
import asyncio.subprocess
import re
import sys
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

    def data_received(self, chunk):
        pass

    async def prepare(self):  # pylint: disable=invalid-overridden-method
        if not sys.flags.dev_mode and not self.request.method == "OPTIONS":
            redis = self.settings.get("REDIS")
            prefix = self.settings.get("REDIS_PREFIX")
            tokens = (
                getattr(self, "RATELIMIT_TOKENS_" + self.request.method, None)
                or self.RATELIMIT_TOKENS
            )
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
                self.set_status(420, "Enhance Your Calm")
                self.write_error(420)

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
        self.finish(
            {
                "status": status_code,
                "message": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    async def prepare(self):
        raise HTTPError(404)


class ZeroDivision(BaseRequestHandler):
    async def prepare(self):
        await super().prepare()
        self.finish(str(0 / 0))
