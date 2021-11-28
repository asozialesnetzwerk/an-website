# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""The utilities module with many helpful things used by other modules."""
from __future__ import annotations

import asyncio
import asyncio.subprocess
import ipaddress
import os
import random
import re
import time
from dataclasses import dataclass, field
from functools import cache
from typing import Any, Callable, Optional, Tuple, Type, TypeVar, Union

import tornado.httputil
from tornado.web import HTTPError, RequestHandler

from an_website import DIR as SITE_BASE_DIR

GIT_URL: str = "https://github.com/asozialesnetzwerk"
REPO_URL: str = f"{GIT_URL}/an-website"

STATIC_DIR: str = os.path.join(SITE_BASE_DIR, "static")
TEMPLATES_DIR: str = os.path.join(SITE_BASE_DIR, "templates")

Handler = Union[
    tuple[str, Type[RequestHandler]],
    tuple[str, Type[RequestHandler], dict[str, Any]],
    tuple[str, Type[RequestHandler], dict[str, Any], str],
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
    # keywords, that can be used for searching
    keywords: tuple[str, ...] = field(default_factory=tuple)
    hidden: bool = False  # whether to hide this page info on the page

    def search(self, query: Union[str, list[str]]) -> float:  # noqa: C901
        """
        Check whether this should be shown on the search page.

        0   → doesn't contain any part of the string
        > 0 → parts of the string are contained, the higher the better
        """
        if self.hidden or self.path is None:
            return 0

        score: float = 0

        if isinstance(query, str):
            words = re.split(r"\s+", query)
            query = query.lower()
            if query in self.description.lower() or query in self.name.lower():
                score = len(query) / 2
        else:
            words = query

        # remove empty strings from words and make the rest lower case
        words = [_w.lower() for _w in words if len(_w) > 0]

        if len(words) == 0:
            # query empty, so find in everything
            return 1.0

        for word in words:
            if len(self.name) > 0 and word in self.name.lower():
                # multiply by 3, so the title it the most important
                score += 3 * (len(word) / len(self.name))
            if len(self.description) > 0 and word in self.description.lower():
                # multiply by 2, so the description it the second important
                score += 2 * (len(word) / len(self.description))

            if word in self.keywords:
                # word is directly in the keywords (really good)
                score += 1
            elif len(self.keywords) > 0:
                # check if word is partly in the key words
                kw_score = 0.0
                for _kw in self.keywords:
                    if word in _kw.lower():
                        kw_score += len(word) / len(_kw)
                score += kw_score / len(self.keywords)

        return score / len(words)


@dataclass(order=True, frozen=True)
class ModuleInfo(PageInfo):
    """
    The module info class adds handlers and sub pages to the page info.

    This gets created by every module to add the handlers.
    """

    handlers: HandlerTuple = field(default_factory=HandlerTuple)
    sub_pages: tuple[PageInfo, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def get_page_info(self, path: str) -> PageInfo:
        """Get the page_info of that specified path."""
        if self.path == path:
            return self

        for page_info in self.sub_pages:
            if page_info.path == path:
                return page_info

        return self

    def get_keywords_as_str(self, path: str) -> str:
        """Get the keywords as comma seperated string."""
        page_info = self.get_page_info(path)
        if self != page_info:
            return ", ".join((*self.keywords, *page_info.keywords))

        return ", ".join(self.keywords)

    def search(self, query: Union[str, list[str]]) -> float:
        score = super().search(query)

        if len(self.sub_pages) > 0:
            sp_score = 0.0
            for page in self.sub_pages:
                sp_score += page.search(query)
            score += sp_score / len(self.sub_pages)

        return score


class Timer:
    """Timer class used for timing stuff."""

    def __init__(self):
        """Start the timer."""
        self._execution_time: Optional[float] = None
        self._start_time: float = time.perf_counter()

    def stop(self) -> float:
        """
        Stop the timer and return the execution time in seconds.

        If the timer was stopped already a ValueError gets raised.
        """
        if self._execution_time is not None:
            raise ValueError("Timer has been stopped before.")
        self._execution_time = time.perf_counter() - self._start_time

        del self._start_time
        return self._execution_time

    @property
    def execution_time(self) -> float:
        """
        Get the execution time in seconds and return it.

        If the timer wasn't stopped yet a ValueError gets raised.
        """
        if self._execution_time is None:
            raise ValueError("Timer wasn't stopped yet.")
        return self._execution_time


T = TypeVar("T")  # pylint: disable=invalid-name


@cache
def add_args_to_url(url: str, **kwargs) -> str:
    """Add a query arguments to a url."""
    if len(kwargs) == 0:
        return url

    url_args: dict[str, str] = {}

    for key, value in kwargs.items():
        if value is not None:
            if isinstance(value, bool):
                url_args[key] = bool_to_str(value)
            else:
                url_args[key] = str(value)

    if len(url_args) == 0:
        return url

    return tornado.httputil.url_concat(url, url_args)


def anonymize_ip(ip_address, *, ignore_invalid=False):
    """Anonymize an IP address."""
    try:
        version = ipaddress.ip_address(ip_address).version
    except ValueError:
        if ignore_invalid:
            return ip_address
        raise

    if version == 4:
        return str(
            ipaddress.ip_network(
                ip_address + "/24", strict=False
            ).network_address
        )
    if version == 6:
        return str(
            ipaddress.ip_network(
                ip_address + "/32", strict=False
            ).network_address
        )
    raise HTTPError(reason="ERROR: -41")


def apm_anonymization_processor(  # pylint: disable=unused-argument
    client, event
):
    """Anonymize the APM events."""
    if "context" in event and "request" in event["context"]:
        request = event["context"]["request"]
        if "url" in request and "pathname" in request["url"]:
            if request["url"]["pathname"] == "/robots.txt":
                return event
        if "socket" in request and "remote_address" in request["socket"]:
            request["socket"]["remote_address"] = anonymize_ip(
                request["socket"]["remote_address"]
            )
        if "headers" in request:
            headers = request["headers"]
            if "X-Forwarded-For" in headers:
                if "," in headers["X-Forwarded-For"]:
                    headers["X-Forwarded-For"] = anonymize_ip(
                        headers["X-Forwarded-For"].split(","),
                        ignore_invalid=True,
                    )
                else:
                    headers["X-Forwarded-For"] = anonymize_ip(
                        headers["X-Forwarded-For"], ignore_invalid=True
                    )
            for header in headers:
                if "ip" in header.lower().split("-"):
                    headers[header] = anonymize_ip(
                        headers[header], ignore_invalid=True
                    )
    return event


def bool_to_str(val: bool) -> str:
    """Convert a boolean to sure/nope."""
    return "sure" if val else "nope"


def get_themes() -> tuple[str, ...]:
    """Get a list of available themes."""
    files = os.listdir(os.path.join(STATIC_DIR, "style/themes"))

    return (
        *(file[:-4] for file in files if file.endswith(".css")),
        "random",  # add random to the list of themes
        "random-dark",
    )


def length_of_match(_m: re.Match):
    """Calculate the length of the regex match and return it."""
    span = _m.span()
    return span[1] - span[0]


def n_from_set(_set: Union[set[T], frozenset[T]], _n: int) -> set[T]:
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


async def run(
    programm, *args, stdin=asyncio.subprocess.PIPE
) -> tuple[Optional[int], bytes, bytes]:
    """Run a programm & return the return code, stdout and stderr as tuple."""
    proc = await asyncio.create_subprocess_exec(
        programm,
        *args,
        stdin=stdin,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


def str_to_bool(val: str, default: Optional[bool] = None) -> bool:
    """Convert a string representation of truth to True or False."""
    if isinstance(val, bool):
        return val
    val = val.lower()
    if val in ("sure", "y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("nope", "n", "no", "f", "false", "off", "0"):
        return False
    if val in ("maybe", "idc"):
        return random.choice((True, False))
    if default is None:
        raise ValueError(f"invalid truth value '{val}'")
    return default


def time_function(function: Callable[..., T], *args: Any) -> tuple[T, float]:
    """Run the function and return the result and the time it took in s."""
    timer = Timer()
    return function(*args), timer.stop()


THEMES: tuple[str, ...] = get_themes()
