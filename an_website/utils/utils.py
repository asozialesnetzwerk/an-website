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
import time
from base64 import b85encode
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntFlag
from functools import cache
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from typing import IO, Any, Literal, TypeVar, Union
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

import elasticapm  # type: ignore[import]
import regex
from blake3 import blake3  # type: ignore[import]
from elasticsearch import AsyncElasticsearch
from Levenshtein import distance  # type: ignore[import]
from redis.asyncio import Redis
from tornado.web import HTTPError, RequestHandler

from .. import STATIC_DIR

T = TypeVar("T")

# pylint: disable=consider-alternative-union-syntax
Handler = Union[
    tuple[str, type[RequestHandler]],
    tuple[str, type[RequestHandler], dict[str, Any]],
    tuple[str, type[RequestHandler], dict[str, Any], str],
]

OpenMojiValue = Literal[False, "img"]  # , "font"]

SUS_PATHS = {
    "/-profiler/phpinfo",
    "/.aws/credentials",
    "/.env",
    "/.env.bak",
    "/.ftpconfig",
    "/admin/controller/extension/extension",
    "/assets/filemanager/dialog",
    "/assets/vendor/server/php",
    "/aws.yml",
    "/boaform/admin/formlogin",
    "/phpinfo",
    "/public/assets/jquery-file-upload/server/php",
    "/root",
    "/settings/aws.yml",
    "/uploads",
    "/vendor/phpunit/phpunit/src/util/php/eval-stdin",
    "/wordpress",
    "/wp",
    "/wp-admin",
    "/wp-admin/css",
    "/wp-includes",
    "/wp-login",
    "/wp-upload",
}


class Permission(IntFlag):
    """Permissions for accessing restricted stuff."""

    RATELIMITS = 1
    TRACEBACK = 2
    BACKDOOR = 4
    UPDATE = 8
    REPORTING = 16


# sortable, so the pages can be linked in an order
# frozen, so it's immutable
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

    def search(self, query: str | Sequence[str]) -> float:  # noqa: C901
        # pylint: disable=too-complex
        """
        Check whether this should be shown on the search page.

        0   → doesn't contain any part of the string
        > 0 → parts of the string are contained, the higher, the better
        """
        if self.hidden or self.path is None:
            return 0

        score: float = 0
        words: Sequence[str]

        if isinstance(query, str):
            words = regex.split(r"\s+", query)
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

    def get_keywords_as_str(self, path: str) -> str:
        """Get the keywords as comma-seperated string."""
        page_info = self.get_page_info(path)
        if self != page_info:
            return ", ".join((*self.keywords, *page_info.keywords))

        return ", ".join(self.keywords)

    def get_page_info(self, path: str) -> PageInfo:
        """Get the PageInfo of the specified path."""
        if self.path == path:
            return self

        for page_info in self.sub_pages:
            if page_info.path == path:
                return page_info

        return self

    def search(self, query: str | Sequence[str]) -> float:  # noqa: D102
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

    @property
    def execution_time(self) -> float:
        """
        Get the execution time in seconds and return it.

        If the timer wasn't stopped yet a ValueError gets raised.
        """
        if self._execution_time is None:
            raise ValueError("Timer wasn't stopped yet.")
        return self._execution_time

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
    address = address.strip()
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
            path = request["url"]["pathname"]
            if path == "/robots.txt" or path.lower() in SUS_PATHS:
                return event
        if "socket" in request and "remote_address" in request["socket"]:
            request["socket"]["remote_address"] = anonymize_ip(
                request["socket"]["remote_address"]
            )
        if "headers" in request:
            headers = request["headers"]
            if "X-Forwarded-For" in headers:
                headers["X-Forwarded-For"] = ", ".join(
                    anonymize_ip(ip.strip(), ignore_invalid=True)
                    for ip in headers["X-Forwarded-For"].split(",")
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


def country_code_to_flag(code: str) -> str:
    """Convert a two-letter ISO country code to a flag emoji."""
    return "".join(chr(ord(char) + 23 * 29 * 191) for char in code.upper())


def create_emoji_html(emoji: str, emoji_url: str) -> str:
    """Create an HTML element that can be used to display an emoji."""
    return f'<img src="{emoji_url}" alt="{emoji}" class="emoji">'


def emoji2code(emoji: str) -> str:
    """Convert an emoji to the hexcodes of it."""
    return "-".join(f"{ord(c):04x}" for c in emoji).upper()


def emojify(string: str) -> str:
    """Emojify a given string."""
    string = regex.sub(
        r"[a-zA-Z]+",
        lambda match: "\u200C".join(country_code_to_flag(match[0])),
        replace_umlauts(string),
    )
    string = regex.sub(
        r"[0-9#*]+", lambda match: f"{'⃣'.join(match[0])}⃣", string
    )
    return (
        string.replace("!?", "⁉")
        .replace("!!", "‼")
        .replace("?", "❓")
        .replace("!", "❗")
        .replace("-", "➖")
        .replace("+", "➕")
    )


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
        *(file.removesuffix(".css") for file in files if file.endswith(".css")),
        "random",  # add random to the list of themes
        "random-dark",
    )


def hash_bytes(*args: bytes, size: int = 32) -> str:
    """Hash bytes with BLAKE3 and return the Base85 representation."""
    hasher = blake3()
    for spam in args:
        hasher.update(spam)
    digest: bytes = hasher.digest(size)
    return b85encode(digest).decode("ascii")


def hash_ip(address: str | IPv4Address | IPv6Address) -> str:
    """Hash an IP address."""
    if not isinstance(address, IPv4Address | IPv6Address):
        address = ip_address(address)
    return hash_bytes(
        blake3(datetime.utcnow().date().isoformat().encode("ascii")).digest(),
        address.packed,
    )


def length_of_match(match: regex.Match[str]) -> int:
    """Calculate the length of the regex match and return it."""
    span = match.span()
    return span[1] - span[0]


def n_from_set(set_: set[T] | frozenset[T], n: int) -> set[T]:
    """Get and return n elements of the set as a new set."""
    # pylint: disable=invalid-name
    new_set = set()
    for i, element in enumerate(set_):
        if i >= n:
            break
        new_set.add(element)
    return new_set


def name_to_id(val: str) -> str:
    """Replace umlauts and whitespaces in a string to get a valid HTML id."""
    return regex.sub(
        r"[^a-z0-9]+",
        "-",
        replace_umlauts(val).lower(),
    ).strip("-")


def normalized_levenshtein(string1: str, string2: str) -> float:
    """Calculate the normalized Levenshtein distance between two strings."""
    return float(distance(string1, string2)) / max(len(string1), len(string2))


def parse_openmoji_arg(value: str, default: OpenMojiValue) -> OpenMojiValue:
    """Parse the openmoji arg into a Literal."""
    value = value.lower()
    # if value in {"f", "font"}:
    #     return "font"
    if value in {"i", "img"}:
        return "img"
    if value in {"n", "nope"}:
        return False
    return default


async def ratelimit(
    redis: Redis[str],
    redis_prefix: str,
    remote_ip: str,
    *,
    bucket: None | str,
    max_burst: int,
    count_per_period: int,
    period: int,
    tokens: int,
) -> tuple[bool, dict[str, str]]:
    """Take b1nzy to space using Redis."""
    remote_ip = hash_bytes(remote_ip.encode("ascii"))
    key = f"{redis_prefix}:ratelimit:{remote_ip}"
    if bucket:
        key = f"{key}:{bucket}"

    result = await redis.execute_command(
        # type: ignore[no-untyped-call]
        "CL.THROTTLE",
        key,
        max_burst,
        count_per_period,
        period,
        tokens,
    )

    headers: dict[str, str] = {}

    # fmt: off
    # pylint: disable=line-too-long
    if result[0]:
        retry_after = result[3] + 1  # TODO: remove after brandur/redis-cell#58 is merged and a new release was made  # noqa: B950
        headers["Retry-After"] = str(retry_after)
        if not bucket:
            headers["X-RateLimit-Global"] = "true"

    if bucket:
        assert bucket is not None
        reset_after = result[4] + 1  # TODO: remove after brandur/redis-cell#58 is merged and a new release was made  # noqa: B950
        headers["X-RateLimit-Limit"] = str(result[1])
        headers["X-RateLimit-Remaining"] = str(result[2])
        headers["X-RateLimit-Reset"] = str(time.time() + reset_after)
        headers["X-RateLimit-Reset-After"] = str(reset_after)
        headers["X-RateLimit-Bucket"] = hash_bytes(bucket.encode("ascii"))
    # fmt: on

    return bool(result[0]), headers


def remove_suffix_ignore_case(string: str, suffix: str) -> str:
    """Remove a suffix without caring about the case."""
    if string.lower().endswith(suffix.lower()):
        return string[: -len(suffix)]
    return string


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
        raise ValueError(f"invalid truth value {val!r}")
    return default


def time_function(function: Callable[..., T], *args: Any) -> tuple[T, float]:
    """Run the function and return the result and the time it took in s."""
    timer = Timer()
    return function(*args), timer.stop()


THEMES: tuple[str, ...] = get_themes()
