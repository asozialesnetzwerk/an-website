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

"""A module with many useful things used by other modules."""

from __future__ import annotations

import asyncio
import os
import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntFlag
from functools import cache
from ipaddress import ip_address, ip_network
from typing import IO, Any, TypeVar, Union, cast
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

import elasticapm  # type: ignore
from blake3 import blake3  # type: ignore
from elasticsearch import AsyncElasticsearch
from tornado.web import HTTPError, RequestHandler

from .. import STATIC_DIR

T = TypeVar("T")

# pylint: disable=consider-alternative-union-syntax
Handler = Union[
    tuple[str, type[RequestHandler]],
    tuple[str, type[RequestHandler], dict[str, Any]],
    tuple[str, type[RequestHandler], dict[str, Any], str],
]


# sortable so the pages can be linked in an order
# frozen so it's immutable
@dataclass(order=True, frozen=True)
class PageInfo:
    """The PageInfo class that is used for the subpages of a ModuleInfo."""

    name: str
    description: str
    path: None | str = None
    # keywords that can be used for searching
    keywords: tuple[str, ...] = field(default_factory=tuple)
    hidden: bool = False  # whether to hide this page info on the page
    short_name: None | str = None  # short name for the page

    def search(self, query: str | list[str]) -> float:  # noqa: C901
        # pylint: disable=too-complex
        """
        Check whether this should be shown on the search page.

        0   → doesn't contain any part of the string
        > 0 → parts of the string are contained, the higher, the better
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

        # remove empty strings from words and make the rest lowercase
        words = [word.lower() for word in words if len(word) > 0]

        if not words:
            # query empty, so find everything
            return 1.0

        for word in words:
            if len(self.name) > 0 and word in self.name.lower():
                # multiply by 3, so the title is most important
                score += 3 * (len(word) / len(self.name))
            if len(self.description) > 0 and word in self.description.lower():
                # multiply by 2, so the description is second-most important
                score += 2 * (len(word) / len(self.description))

            if word in self.keywords:
                # word is directly in the keywords (really good)
                score += 1
            elif len(self.keywords) > 0:
                # check if word is partially in the keywords
                kw_score = 0.0
                for keyword in self.keywords:
                    if word in keyword.lower():
                        kw_score += len(word) / len(keyword)
                score += kw_score / len(self.keywords)

        return score / len(words)


@dataclass(order=True, frozen=True)
class ModuleInfo(PageInfo):
    """
    The ModuleInfo class adds handlers and subpages to the PageInfo.

    This gets created by every module to add the handlers.
    """

    handlers: tuple[Handler, ...] = field(default_factory=tuple[Handler, ...])
    sub_pages: tuple[PageInfo, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def get_page_info(self, path: str) -> PageInfo:
        """Get the PageInfo of the specified path."""
        if self.path == path:
            return self

        for page_info in self.sub_pages:
            if page_info.path == path:
                return page_info

        return self

    def get_keywords_as_str(self, path: str) -> str:
        """Get the keywords as comma-seperated string."""
        page_info = self.get_page_info(path)
        if self != page_info:
            return ", ".join((*self.keywords, *page_info.keywords))

        return ", ".join(self.keywords)

    def search(self, query: str | list[str]) -> float:
        score = super().search(query)

        if len(self.sub_pages) > 0:
            sp_score = 0.0
            for page in self.sub_pages:
                sp_score += page.search(query)
            score += sp_score / len(self.sub_pages)

        return score


class Timer:
    """Timer class used for timing stuff."""

    def __init__(self) -> None:
        """Start the timer."""
        self._execution_time: None | float = None
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


class Permissions(IntFlag):
    """Permissions for accessing the website."""

    RATELIMITS = 1
    TRACEBACK = 2
    BACKDOOR = 4
    UPDATE = 8


@cache
def add_args_to_url(url: str | SplitResult, **kwargs: dict[str, Any]) -> str:
    # pylint: disable=confusing-consecutive-elif
    """Add query arguments to a URL."""
    if isinstance(url, str):
        url = urlsplit(url)

    if not kwargs:
        return url.geturl()

    url_args: dict[str, str] = dict(
        parse_qsl(url.query, keep_blank_values=True)
    )

    for key, value in kwargs.items():  # type: str, Any
        if value is None:
            if key in url_args:
                del url_args[key]
        elif isinstance(value, bool):
            url_args[key] = bool_to_str(value)
        else:
            url_args[key] = str(value)

    return urlunsplit(
        (
            url.scheme,
            url.netloc,
            url.path,
            urlencode(url_args),
            url.fragment,
        )
    )


def anonymize_ip(address: str, *, ignore_invalid: bool = False) -> str:
    """Anonymize an IP address."""
    try:
        version = ip_address(address).version
    except ValueError:
        if ignore_invalid:
            return address
        raise

    if version == 4:
        return str(ip_network(address + "/24", strict=False).network_address)
    if version == 6:
        return str(ip_network(address + "/32", strict=False).network_address)

    raise HTTPError(reason="ERROR: -41")


def apm_anonymization_processor(  # pylint: disable=unused-argument
    client: elasticapm.Client, event: dict[str, Any]
) -> dict[str, Any]:
    """Anonymize an APM event."""
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


def emojify(string: str) -> str:
    """Emojify a given string."""
    string = re.sub(
        r"[a-zA-Z]+",
        lambda match: "\u200C".join(country_code_to_flag(match.group(0))),
        replace_umlauts(string),
    )
    string = re.sub(
        r"[0-9#*]+", lambda match: f"{'⃣'.join(match.group(0))}⃣", string
    )
    return (
        string.replace("!?", "⁉")
        .replace("!!", "‼")
        .replace("?", "❓")
        .replace("!", "❗")
        .replace("-", "➖")
        .replace("+", "➕")
    )


def country_code_to_flag(code: str) -> str:
    """Convert a two-letter ISO country code to a flag emoji."""
    return "".join(chr(ord(char) + 23 * 29 * 191) for char in code.upper())


async def geoip(
    ip: str,  # pylint: disable=invalid-name
    database: str = "GeoLite2-City.mmdb",
    elasticsearch: None | AsyncElasticsearch = None,
    *,
    geoip_cache: dict[str, dict[str, dict[str, Any]]] = {},  # noqa: B006
) -> None | dict[str, Any]:
    """Get GeoIP information."""
    if ip not in geoip_cache:
        geoip_cache[ip] = {}

    if database not in geoip_cache[ip]:

        if not elasticsearch:
            return None

        properties: None | tuple[str, ...]

        if database == "GeoLite2-City.mmdb":
            properties = (
                "continent_name",
                "country_iso_code",
                "country_name",
                "region_iso_code",
                "region_name",
                "city_name",
                "location",
                "timezone",
            )
        elif database == "GeoLite2-Country.mmdb":
            properties = (
                "continent_name",
                "country_iso_code",
                "country_name",
            )
        elif database == "GeoLite2-ASN.mmdb":
            properties = ("asn", "network", "organization_name")
        else:
            properties = None

        geoip_cache[ip][database] = (
            await elasticsearch.ingest.simulate(
                body={
                    "pipeline": {
                        "processors": [
                            {
                                "geoip": {
                                    "field": "ip",
                                    "database_file": database,
                                    "properties": properties,
                                }
                            }
                        ]
                    },
                    "docs": [{"_source": {"ip": ip}}],
                },
                params={"filter_path": "docs.doc._source"},
            )
        )["docs"][0]["doc"]["_source"].get("geoip", {})
        if "country_iso_code" in geoip_cache[ip][database]:
            geoip_cache[ip][database]["country_flag"] = country_code_to_flag(
                geoip_cache[ip][database]["country_iso_code"]
            )
    return geoip_cache[ip][database]


def get_themes() -> tuple[str, ...]:
    """Get a list of available themes."""
    files = os.listdir(os.path.join(STATIC_DIR, "style/themes"))

    return (
        *(file[:-4] for file in files if file.endswith(".css")),
        "random",  # add random to the list of themes
        "random-dark",
    )


def hash_ip(ip: str) -> str:  # pylint: disable=invalid-name
    """Hash an IP address."""
    return cast(
        str,
        blake3(
            ip.encode("ascii")
            + blake3(
                datetime.utcnow().date().isoformat().encode("ascii")
            ).digest()
        ).hexdigest(),
    )


def length_of_match(_m: re.Match[str]) -> int:
    """Calculate the length of the regex match and return it."""
    span = _m.span()
    return span[1] - span[0]


def n_from_set(_set: set[T] | frozenset[T], _n: int) -> set[T]:
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


def name_to_id(val: str) -> str:
    """Replace umlauts and whitespaces in a string to get a valid HTML id."""
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        replace_umlauts(val).lower(),
    ).strip("-")


def replace_umlauts(string: str) -> str:
    """Replace Ä, Ö, Ü, ẞ, ä, ö, ü, ß in string."""
    if string.isupper():
        return (
            string.replace("Ä", "AE")
            .replace("Ö", "OE")
            .replace("Ü", "UE")
            .replace("ẞ", "SS")
        )
    if " " in string:
        return " ".join(replace_umlauts(word) for word in string.split(" "))
    return (
        string.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
        .replace("ẞ", "SS")
    )


async def run(
    program: str,
    *args: str,
    stdin: int | IO[Any] = asyncio.subprocess.DEVNULL,
    stdout: None | int | IO[Any] = asyncio.subprocess.PIPE,
    stderr: None | int | IO[Any] = asyncio.subprocess.PIPE,
    **kwargs: Any,
) -> tuple[None | int, bytes, bytes]:
    """Run a programm and return the exit code, stdout and stderr as tuple."""
    proc = await asyncio.create_subprocess_exec(
        program,
        *args,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
        **kwargs,
    )

    output = await proc.communicate()
    return proc.returncode, *output


def str_to_bool(val: None | str | bool, default: None | bool = None) -> bool:
    """Convert a string representation of truth to True or False."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        val = val.lower()
        if val in {"1", "on", "s", "sure", "t", "true", "y", "yes"}:
            return True
        if val in {"0", "f", "false", "n", "no", "nope", "off"}:
            return False
        if val in {"idc", "maybe", "random"}:
            return bool(random.randrange(2))
    if default is None:
        raise ValueError(f"Invalid truth value: {val}")
    return default


def time_function(function: Callable[..., T], *args: Any) -> tuple[T, float]:
    """Run the function and return the result and the time it took in s."""
    timer = Timer()
    return function(*args), timer.stop()


THEMES: tuple[str, ...] = get_themes()
