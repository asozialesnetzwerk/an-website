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

import argparse
import asyncio
import contextlib
import heapq
import logging
import os
import pathlib
import random
import sys
import time
from base64 import b85encode
from collections.abc import Awaitable, Callable, Generator, Iterable, Set
from configparser import ConfigParser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntFlag
from functools import cache, partial
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from pathlib import Path
from typing import (
    IO,
    Any,
    Final,
    Literal,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
)
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

import elasticapm  # type: ignore[import-untyped]
import regex
from blake3 import blake3  # type: ignore[import-untyped]
from elasticsearch import AsyncElasticsearch, ElasticsearchException
from geoip import geolite2  # type: ignore[import-untyped]
from rapidfuzz.distance.Levenshtein import normalized_distance
from redis.asyncio import Redis
from tornado.web import HTTPError, RequestHandler
from UltraDict import UltraDict  # type: ignore[import-untyped]

from .. import DIR as ROOT_DIR
from .. import STATIC_DIR

LOGGER: Final = logging.getLogger(__name__)

T = TypeVar("T")

T_Val = TypeVar("T_Val")  # pylint: disable=invalid-name

TOptionalStr = TypeVar(  # pylint: disable=invalid-name
    "TOptionalStr", None, str
)

# pylint: disable=consider-alternative-union-syntax
Handler: TypeAlias = Union[
    tuple[str, type[RequestHandler]],
    tuple[str, type[RequestHandler], dict[str, Any]],
    tuple[str, type[RequestHandler], dict[str, Any], str],
]

OpenMojiValue: TypeAlias = Literal[False, "img"]  # , "font"]
BumpscosityValue: TypeAlias = Literal[0, 1, 12, 50, 76, 100, 1000]
BUMPSCOSITY_VALUES: Final[tuple[BumpscosityValue, ...]] = get_args(
    BumpscosityValue
)

PRINT = int.from_bytes(Path(ROOT_DIR, "primes.bin").read_bytes(), "big")

IP_HASH_SALT: Final = {
    "date": datetime.now(timezone.utc).date(),
    "hasher": blake3(
        blake3(
            datetime.now(timezone.utc).date().isoformat().encode("ASCII")
        ).digest()
    ),
}

SUS_PATHS: Final[Set[str]] = {
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


class AwaitableValue(Awaitable[T_Val]):
    # pylint: disable=too-few-public-methods
    """An awaitable that always returns the same value."""

    def __await__(self) -> Generator[None, None, T_Val]:
        """Return an iterator returning the value."""
        yield
        return self._value

    def __init__(self, value: T_Val) -> None:
        """Set the value."""
        self._value = value


class Permission(IntFlag):
    """Permissions for accessing restricted stuff."""

    RATELIMITS = 1
    TRACEBACK = 2
    BACKDOOR = 4
    UPDATE = 8
    REPORTING = 16
    SHORTEN = 32
    UPLOAD = 64


# sortable, so the pages can be linked in an order
# frozen, so it's immutable
@dataclass(order=True, frozen=True, slots=True)
class PageInfo:
    """The PageInfo class that is used for the subpages of a ModuleInfo."""

    name: str
    description: str
    path: None | str = None
    # keywords that can be used for searching
    keywords: tuple[str, ...] = field(default_factory=tuple)
    hidden: bool = False  # whether to hide this page info on the page
    short_name: None | str = None  # short name for the page


@dataclass(order=True, frozen=True, slots=True)
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


class Timer:
    """Timer class used for timing stuff."""

    __slots__ = ("_execution_time", "_start_time")

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
        return self._execution_time


@cache
def add_args_to_url(url: str | SplitResult, **kwargs: Any) -> str:
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


def anonymize_ip(
    address: TOptionalStr, *, ignore_invalid: bool = False
) -> TOptionalStr:
    """Anonymize an IP address."""
    if address is None:
        return None

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
        return str(ip_network(address + "/48", strict=False).network_address)

    raise HTTPError(reason="ERROR: -41")


def apm_anonymization_processor(  # type: ignore[no-any-unimported]
    client: elasticapm.Client,  # pylint: disable=unused-argument
    event: dict[str, Any],
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
    return f"<img src={emoji_url!r} alt={emoji!r} class='emoji'>"


def emoji2code(emoji: str) -> str:
    """Convert an emoji to the hexcodes of it."""
    return "-".join(f"{ord(c):04x}" for c in emoji).upper()


def emoji2html(emoji: str) -> str:
    """Convert an emoji to HTML."""
    return create_emoji_html(
        emoji, f"/static/img/openmoji-svg-14.0/{emoji2code(emoji)}.svg"
    )


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
    ip: None | str,
    database: str = "GeoLite2-City.mmdb",
    elasticsearch: None | AsyncElasticsearch = None,
    *,
    allow_fallback: bool = True,
    caches: dict[str, dict[str, dict[str, Any]]] = UltraDict(),  # noqa: B008
) -> None | dict[str, Any]:
    """Get GeoIP information."""
    # pylint: disable=too-complex
    if not ip:
        return None

    cache = caches.get(ip, {})  # pylint: disable=redefined-outer-name
    if database not in cache:
        if not elasticsearch:
            if allow_fallback and database in {
                "GeoLite2-City.mmdb",
                "GeoLite2-Country.mmdb",
            }:
                return geoip_fallback(
                    ip, country=database == "GeoLite2-City.mmdb"
                )
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

        try:
            cache[database] = (
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
        except ElasticsearchException:
            if allow_fallback and database in {
                "GeoLite2-City.mmdb",
                "GeoLite2-Country.mmdb",
            }:
                return geoip_fallback(
                    ip, country=database == "GeoLite2-City.mmdb"
                )
            raise

        if "country_iso_code" in cache[database]:
            cache[database]["country_flag"] = country_code_to_flag(
                cache[database]["country_iso_code"]
            )

        caches[ip] = cache
    return cache[database]


def geoip_fallback(ip: str, country: bool = False) -> None | dict[str, Any]:
    """Get GeoIP information without using Elasticsearch."""
    if not (info := geolite2.lookup(ip)):
        return None

    info_dict = info.get_info_dict()

    continent_name = info_dict.get("continent", {}).get("names", {}).get("en")
    country_iso_code = info_dict.get("country", {}).get("iso_code")
    country_name = info_dict.get("country", {}).get("names", {}).get("en")

    data = {
        "continent_name": continent_name,
        "country_iso_code": country_iso_code,
        "country_name": country_name,
    }

    if data["country_iso_code"]:
        data["country_flag"] = country_code_to_flag(data["country_iso_code"])

    if country:
        for key, value in tuple(data.items()):
            if not value:
                del data[key]

        return data

    latitude = info_dict.get("location", {}).get("latitude")
    longitude = info_dict.get("location", {}).get("longitude")
    location = (latitude, longitude) if latitude and longitude else None
    time_zone = info_dict.get("location", {}).get("time_zone")

    data.update({"location": location, "timezone": time_zone})

    for key, value in tuple(data.items()):
        if not value:
            del data[key]

    return data


def get_themes() -> tuple[str, ...]:
    """Get a list of available themes."""
    files = os.listdir(os.path.join(STATIC_DIR, "css/themes"))
    return (
        *(file[:-4] for file in files if file.endswith(".css")),
        "random",  # add random to the list of themes
        "random_dark",
    )


def hash_bytes(*args: bytes, hasher: Any = None, size: int = 32) -> str:
    """Hash bytes and return the Base85 representation."""
    digest: bytes
    if not hasher:
        hasher = blake3()
    for arg in args:
        hasher.update(arg)
    digest = (
        hasher.digest(size)
        if isinstance(hasher, blake3)
        else hasher.digest()[:size]
    )
    return b85encode(digest).decode("ASCII")


def hash_ip(
    address: None | str | IPv4Address | IPv6Address, size: int = 32
) -> str:
    """Hash an IP address."""
    if isinstance(address, str):
        address = ip_address(address)
    if IP_HASH_SALT["date"] != (date := datetime.now(timezone.utc).date()):
        IP_HASH_SALT["hasher"] = blake3(
            blake3(date.isoformat().encode("ASCII")).digest()
        )
        IP_HASH_SALT["date"] = date
    return hash_bytes(
        address.packed if address else b"",
        hasher=IP_HASH_SALT["hasher"].copy(),
        size=size,
    )


def is_in_european_union(ip: None | str) -> None | bool:
    """Return whether the specified address is in the EU."""
    if not (ip and (info := geolite2.lookup(ip))):
        return None

    return cast(bool, info.get_info_dict().get("is_in_european_union", False))


def is_prime(number: int) -> bool:
    """Return whether the specified number is prime."""
    if not number % 2:
        return number == 2
    return bool(PRINT & (1 << (number // 2)))


def length_of_match(match: regex.Match[Any]) -> int:
    """Calculate the length of the regex match and return it."""
    return match.end() - match.start()


def n_from_set(set_: Set[T], n: int) -> set[T]:
    """Get and return n elements of the set as a new set."""
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


def get_close_matches(  # based on difflib.get_close_matches
    word: str,
    possibilities: Iterable[str],
    count: int = 3,
    cutoff: float = 0.5,
) -> tuple[str, ...]:
    """Use normalized_distance to return list of the best "good enough" matches.

    word is a sequence for which close matches are desired (typically a string).

    possibilities is a list of sequences against which to match word
    (typically a list of strings).

    Optional arg count (default 3) is the maximum number of close matches to
    return.  count must be > 0.

    Optional arg cutoff (default 0.5) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.

    The best (no more than count) matches among the possibilities are returned
    in a tuple, sorted by similarity score, most similar first.
    """
    if count <= 0:
        raise ValueError(f"count must be > 0: {count}")
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError(f"cutoff must be in [0.0, 1.0]: {cutoff}")
    result: list[tuple[float, str]] = []
    for possibility in possibilities:
        ratio: float = normalized_distance(possibility, word)
        if ratio <= cutoff:
            result.append((ratio, possibility))
    # Strip scores for the best count matches
    return tuple(word for score, word in heapq.nsmallest(count, result))


def parse_bumpscosity(value: str | int | None) -> BumpscosityValue:
    """Parse a string to a valid bumpscosity value."""
    if isinstance(value, str):
        with contextlib.suppress(ValueError):
            value = int(value, base=0)
    if value in BUMPSCOSITY_VALUES:
        return cast(BumpscosityValue, value)
    return random.Random(repr(value)).choice(BUMPSCOSITY_VALUES)


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


async def ratelimit(  # pylint: disable=too-many-arguments
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
    remote_ip = hash_bytes(remote_ip.encode("ASCII"))
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

    now = time.time()

    headers: dict[str, str] = {}

    if result[0]:
        headers["Retry-After"] = str(result[3])
        if not bucket:
            headers["X-RateLimit-Global"] = "true"

    if bucket:
        headers["X-RateLimit-Limit"] = str(result[1])
        headers["X-RateLimit-Remaining"] = str(result[2])
        headers["X-RateLimit-Reset"] = str(now + result[4])
        headers["X-RateLimit-Reset-After"] = str(result[4])
        headers["X-RateLimit-Bucket"] = hash_bytes(bucket.encode("ASCII"))

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
        if val in {
            "1",
            "a",
            "accept",
            "e",
            "enabled",
            "on",
            "s",
            "sure",
            "t",
            "true",
            "y",
            "yes",
        }:
            return True
        if val in {
            "0",
            "d",
            "disabled",
            "f",
            "false",
            "n",
            "no",
            "nope",
            "off",
            "r",
            "reject",
        }:
            return False
        if val in {"idc", "maybe", "random"}:
            return bool(random.randrange(2))  # nosec: B311
    if default is None:
        raise ValueError(f"Invalid bool value: {val!r}")
    return default


def str_to_set(string: str) -> set[str]:
    """Convert a string to a set of strings."""
    return {part.strip() for part in string.split(",") if part.strip()}


class ArgparseNamespace(argparse.Namespace):
    """A class to fake type hints for argparse Namespace."""

    # pylint: disable=too-few-public-methods
    __slots__ = ("config", "save_config_to")

    config: list[pathlib.Path]
    save_config_to: pathlib.Path | None


def create_argument_parser() -> argparse.ArgumentParser:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        default=[pathlib.Path("config.ini")],
        help="the path to the config file",
        metavar="PATH",
        nargs="*",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--save-config-to",
        default=None,
        help="save the configuration to a file",
        metavar="Path",
        nargs="?",
        type=pathlib.Path,
    )
    return parser


def get_arguments_without_help() -> tuple[str, ...]:
    """Get arguments without help."""
    return tuple(arg for arg in sys.argv[1:] if arg not in {"-h", "--help"})


class BetterConfigParser(ConfigParser):
    """A better config parser."""

    getset: Callable[..., set[str]]
    _arg_parser: None | argparse.ArgumentParser
    _arg_parser_options_added: set[tuple[str, str]]
    _all_options_should_be_parsed: bool

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Initialize this config parser."""
        self._arg_parser_options_added = set()
        self._arg_parser = None
        self._all_options_should_be_parsed = False
        converters = kwargs.setdefault("converters", {})
        converters["set"] = str_to_set
        kwargs.setdefault("interpolation", None)
        kwargs["dict_type"] = dict
        super().__init__(*args, **kwargs)

    def _add_fallback_to_config(
        self,
        section: str,
        option: str,
        fallback: str | Iterable[str] | bool | int | float | None,
    ) -> None:
        if section in self and option in self[section]:
            return
        fallback = self._val_to_str(fallback)
        if fallback is None:
            fallback = ""
            option = f"#{option}"
        if section not in self.sections():
            self.add_section(section)
        self.set(section, option.lower(), fallback)

    def _get_conv(
        self, section: str, option: str, conv: Callable[[str], T], **kwargs: Any
    ) -> T:
        self._add_fallback_to_config(section, option, kwargs.get("fallback"))
        if (val := self._get_from_args(section, option, conv)) is not None:
            return val
        return cast(T, super()._get_conv(section, option, conv, **kwargs))

    def _get_from_args(
        self, section: str, option: str, conv: Callable[[str], T]
    ) -> None | T:
        """Try to get the value from the command line arguments."""
        if self._arg_parser is None:
            return None
        option_name = f"{section}-{option}".lower().removeprefix("general-")
        if (section, option) not in self._arg_parser_options_added:
            if self._all_options_should_be_parsed:
                LOGGER.error(
                    "Option %r in section %r should have been queried before.",
                    option,
                    section,
                )
            self._arg_parser.add_argument(
                f"--{option_name}".replace("_", "-"),
                required=False,
                type=conv,
                help=f"Override {option!r} in the {section!r} section of the config",
            )
            self._arg_parser_options_added.add((section, option))
        value = getattr(
            self._arg_parser.parse_known_args(get_arguments_without_help())[0],
            option_name.replace("-", "_"),
            None,
        )
        if value is None:
            return None
        self.set(section, option, self._val_to_str(value))
        return cast(T, value)

    def _val_to_str(self, value: object | None) -> str | None:
        """Convert a value to a string."""
        if value is None or isinstance(value, str):
            return value
        if isinstance(value, Iterable):
            return ", ".join(
                [cast(str, self._val_to_str(val)) for val in value]
            )
        if isinstance(value, bool):
            return bool_to_str(value)
        return str(value)  # float, int

    def add_override_argument_parser(
        self, parser: argparse.ArgumentParser
    ) -> None:
        """Add an argument parser to override config values."""
        self._arg_parser = parser

    def get(self, section: str, option: str, **kwargs: Any) -> None | str:  # type: ignore[override]  # noqa: B950
        """Get an option in a section."""
        self._add_fallback_to_config(section, option, kwargs.get("fallback"))
        if (val := self._get_from_args(section, option, str)) is not None:
            return val
        return cast("None | str", super().get(section, option, **kwargs))

    def set_all_options_should_be_parsed(self) -> None:
        """Set all options should be parsed."""
        self._all_options_should_be_parsed = True


def parse_config(*path: pathlib.Path) -> BetterConfigParser:
    """Parse the config at the given path."""
    config = BetterConfigParser()
    config.read(path, encoding="UTF-8")
    return config


def time_function(function: Callable[..., T], *args: Any) -> tuple[T, float]:
    """Run the function and return the result and the time it took in s."""
    timer = Timer()
    return function(*args), timer.stop()


THEMES: Final[tuple[str, ...]] = get_themes()

ansi_replace = partial(regex.sub, "\033" + r"\[-?\d+[a-zA-Z]", "")
ansi_replace.__doc__ = "Remove ANSI escape sequences from a string."

backspace_replace = partial(regex.sub, ".?\x08", "")
backspace_replace.__doc__ = "Remove backspaces from a string."


def apply(value: T_Val, fun: Callable[[T_Val], T]) -> T:
    """Apply a function to a value and return the result."""
    return fun(value)
