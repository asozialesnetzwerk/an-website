"""The utilities module with many helpful things used by other modules."""
from __future__ import annotations

import asyncio
import asyncio.subprocess
import logging
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Tuple, Union

from ansi2html import Ansi2HTMLConverter  # type: ignore
from tornado import httputil
from tornado.web import HTTPError, RequestHandler

Handler = Union[
    tuple[str, Any],
    tuple[str, Any, dict[str, Any]],
    tuple[str, Any, dict[str, Any], str],
]
# following should be tuple[Handler, ...] but mypy then complains
HandlerTuple = Tuple[Handler, ...]


# sortable so the pages can be linked in a order
# frozen so it's immutable
@dataclass(order=True, frozen=True)
class PageInfo:
    """The page info class that is used for the subpages of a module info."""

    name: str
    description: str
    path: Optional[str] = None


@dataclass(order=True, frozen=True)
class ModuleInfo(PageInfo):
    """
    The module info class that adds handles and sub pages to the page
    info.

    This gets created by every module to add the handlers.
    """

    handlers: HandlerTuple = field(default_factory=HandlerTuple)
    sub_pages: Optional[tuple[PageInfo, ...]] = None


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        "Utilitys",
        "Nütliche Werkzeuge für alle möglichen Sachen.",
        handlers=(
            (r"/error/?", ZeroDivision, {}),
            (r"/([1-5][0-9]{2}).html", ErrorPage, {})
        ),
    )


def length_of_match(_m: re.Match):
    """Calculate the length of the regex match and return it."""
    span = _m.span()
    return span[1] - span[0]


def n_from_set(_set: set, _n: int) -> set:
    """Get and return _n elements of the set as a new set."""
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


async def run(
    cmd, stdin=asyncio.subprocess.PIPE
) -> tuple[Optional[int], bytes, bytes]:
    """
    Run the cmd as a subprocess and return the return code, stdout and
    stderr in a tuple.
    """
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=stdin,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    com = proc.communicate()

    # debugging stuff:
    if "ps -p" not in cmd:
        with open(f"/proc/{proc.pid}/stat") as file:
            print(file.read())
        await (run(f"ps -p {proc.pid} all | grep -E 'PID|{proc.pid}'"))

    # important:
    stdout, stderr = await com

    # debugging stuff:
    if "ps -p" in cmd:
        logger = logging.getLogger(__name__)
        logger.error(
            str(
                {
                    "code": proc.returncode,
                    "stdout": stdout.decode("utf-8"),
                    "stderr": stderr.decode("utf-8"),
                }
            )
        )

    return proc.returncode, stdout, stderr


class BaseRequestHandler(RequestHandler):
    """The base tornado request handler used by every page."""

    RATELIMIT_TOKENS = 1  # can be overridden in subclasses
    title = "Das Asoziale Netzwerk"
    description = "Die tolle Webseite des Asozialen Netzwerkes"

    def initialize(self, **kwargs):
        """
        Get title and description from the kwargs and override the
        default values if they are present.
        """
        self.title = kwargs.get("title", self.title)
        self.description = kwargs.get("description", self.description)

    def data_received(self, chunk):
        """Do nothing."""
        pass

    async def prepare(self):  # pylint: disable=invalid-overridden-method
        """Check rate limits with redis."""
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
        """
        Render the error as a html page with the status code and the
        reason extracted from the kwargs.
        """
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
        )

    def get_error_message(self, **kwargs):
        """
        Get the error message and return it.

        If the server_traceback setting is true (debug mode is activated)
        the traceback gets returned.
        """
        if "exc_info" in kwargs and not issubclass(
            kwargs["exc_info"][0], HTTPError
        ):
            if self.settings.get("serve_traceback"):
                return "".join(traceback.format_exception(*kwargs["exc_info"]))
            return traceback.format_exception_only(*kwargs["exc_info"][:2])[-1]
        return self._reason

    def get_no_3rd_party(self) -> bool:
        """Return the no_3rd_party query argument as boolean."""
        return self.get_query_argument_as_bool("no_3rd_party", False)

    def get_template_namespace(self):
        """Add useful things to the template namespace that are needed by
        most of the pages (like title and description) and return it."""
        namespace = super().get_template_namespace()
        no_3rd_party: bool = self.get_no_3rd_party()
        form_appendix: str = (
            "<input name='no_3rd_party' style='display: none;"
            + "width: 0; height: 0; opacity: 0' value='sure'>"
            if no_3rd_party
            else ""
        )
        namespace.update(
            {
                "ansi2html": Ansi2HTMLConverter(inline=True, scheme="xterm"),
                "title": self.title,
                "description": self.description,
                "no_3rd_party": no_3rd_party,
                "lang": "de",  # can change in future
                "url_appendix": "?no_3rd_party=sure" if no_3rd_party else "",
                "form_appendix": form_appendix,
                # this is not important because we don't need the templates
                # in a context without the request for soundboard and wiki
                "url": self.request.full_url(),
                "settings": self.settings,
            }
        )
        return namespace

    def get_query_argument_as_bool(self, name: str, default: bool = False):
        """Get a query argument by name as boolean with out throwing an error
        and returning the default (by default False) if the argument isn't
        found or not a boolean value specified by the strtobool function."""
        if name not in self.request.query_arguments:
            return default
        try:
            return strtobool(str(self.get_query_argument(name)))
        except ValueError:
            return default


class APIRequestHandler(BaseRequestHandler):
    """The base api request handler that overrides
    the write error method to return errors as json."""

    def write_error(self, status_code, **kwargs):
        """Finish with the status code and the reason as dict"""
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    """
    The default request handler that is used to return 404 if the page
    isn't found.
    """

    RATELIMIT_TOKENS = 0

    async def prepare(self):
        """Throw a 404 http error."""
        raise HTTPError(404)


class ErrorPage(BaseRequestHandler):
    """A request handler that throws an error."""

    RATELIMIT_TOKENS = 0

    async def get(self, code: str):
        """Raise the error_code."""
        status_code: int = int(code)
        self.set_status(status_code)
        self.write_error(status_code)


class ZeroDivision(BaseRequestHandler):
    """A fun request handler that throws an error."""

    RATELIMIT_TOKENS = 10

    async def prepare(self):
        """Divide by zero and throw an error."""
        if not self.request.method == "OPTIONS":
            await super().prepare()
            await self.finish(str(0 / 0))
