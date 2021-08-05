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
from urllib.parse import quote_plus

from ansi2html import Ansi2HTMLConverter  # type: ignore
from tornado import httputil
from tornado.web import HTTPError, RequestHandler

GIT_URL: str = "https://github.com/asozialesnetzwerk"
REPO_URL: str = f"{GIT_URL}/an-website"

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
    The module info class adds handlers and sub pages to the page info.

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
            (r"/([1-5][0-9]{2}).html", ErrorPage, {}),
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
    """Run the cmd and return the return code, stdout and stderr in a tuple."""
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
        Get title and description from the kwargs.

        If title and description are present in the kwargs they
        override self.title and self.description.
        """
        self.title = kwargs.get("title", self.title)
        self.description = kwargs.get("description", self.description)

    def data_received(self, chunk):
        """Do nothing."""

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
        """Render the error page with the status_code as a html page."""
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

    def fix_url(self, url: str, this_url: str = None) -> str:
        """
        Fix an url and return it.

        If the url is from another website, link to it with the redirect page.
        Otherwise just return the url with no_3rd_party appended.
        """
        if this_url is None:
            this_url = self.request.full_url()

        if url.startswith("http") and f"//{self.request.host_name}" not in url:
            # url is to other website:
            return (
                f"/redirect?to={quote_plus(url)}&from"
                f"={quote_plus(this_url)}"
            )

        if self.get_no_3rd_party():
            return url + (
                # if "?" already is in the url then use &
                ("&" if "?" in url else "?")
                + "no_3rd_party=sure"
            )

        return url

    def get_template_namespace(self):
        """
        Add useful things to the template namespace and return it.

        They are mostly needed by most of the pages (like title,
        description and no_3rd_party).
        """
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
                "form_appendix": form_appendix,
                "fix_url": self.fix_url,
                "REPO_URL": self.fix_url(REPO_URL),
                # this is not important because we don't need the templates
                # in a context without the request for soundboard and wiki
                "url": self.request.full_url(),
                "settings": self.settings,
            }
        )
        return namespace

    def get_query_argument_as_bool(self, name: str, default: bool = False):
        """
        Get a query argument by name as boolean with out throwing an error.

        If the argument isn't found or not a boolean value specified by the
        strtobool function return the default (by default False)
        """
        if name not in self.request.query_arguments:
            return default
        try:
            return strtobool(str(self.get_query_argument(name)))
        except ValueError:
            return default


class APIRequestHandler(BaseRequestHandler):
    """
    The base api request handler.

    It overrides the write error method to return errors as json.
    """

    def write_error(self, status_code, **kwargs):
        """Finish with the status code and the reason as dict."""
        self.finish(
            {
                "status": status_code,
                "reason": self.get_error_message(**kwargs),
            }
        )


class NotFound(BaseRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

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

        # get the reason
        reason: str = httputil.responses.get(status_code, "")

        # set the status code if tornado doesn't throw an error if it is set
        if status_code not in (204, 304) and not 100 <= status_code < 200:
            # set the status code
            self.set_status(status_code)

        return await self.render(
            "error.html",
            status=status_code,
            reason=reason,
        )


class ZeroDivision(BaseRequestHandler):
    """A fun request handler that throws an error."""

    RATELIMIT_TOKENS = 10

    async def prepare(self):
        """Divide by zero and throw an error."""
        if not self.request.method == "OPTIONS":
            await super().prepare()
            await self.finish(str(0 / 0))
