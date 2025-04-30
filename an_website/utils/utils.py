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
import bisect
import contextlib
import logging
import pathlib
import random
import sys
import time
from base64 import b85encode
from collections.abc import (
    Awaitable,
    Callable,
    Collection,
    Generator,
    Iterable,
    Mapping,
    Set,
)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntFlag
from functools import cache, partial
from hashlib import sha1
from importlib.resources.abc import Traversable
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from pathlib import Path
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    TypeAlias,
    Union,
    cast,
    get_args,
)
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit

import elasticapm
import regex
from blake3 import blake3
from elastic_transport import ApiError, TransportError
from elasticsearch import AsyncElasticsearch
from geoip import geolite2  # type: ignore[import-untyped]
from openmoji_dist import VERSION as OPENMOJI_VERSION
from rapidfuzz.distance.Levenshtein import distance
from redis.asyncio import Redis
from tornado.web import HTTPError, RequestHandler
from typed_stream import Stream
from UltraDict import UltraDict  # type: ignore[import-untyped]

from .. import DIR as ROOT_DIR, pytest_is_running

if TYPE_CHECKING:
    from .background_tasks import BackgroundTask

LOGGER: Final = logging.getLogger(__name__)

# pylint: disable-next=consider-alternative-union-syntax
type Handler = Union[
    tuple[str, type[RequestHandler]],
    tuple[str, type[RequestHandler], dict[str, Any]],
    tuple[str, type[RequestHandler], dict[str, Any], str],
]

type OpenMojiValue = Literal[False, "img", "glyf_colr1", "glyf_colr0"]
BumpscosityValue: TypeAlias = Literal[0, 1, 12, 50, 76, 100, 1000]
BUMPSCOSITY_VALUES: Final[tuple[BumpscosityValue, ...]] = get_args(
    BumpscosityValue
)

PRINT = int.from_bytes((ROOT_DIR / "primes.bin").read_bytes(), "big")

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


class ArgparseNamespace(argparse.Namespace):
    """A class to fake type hints for argparse.Namespace."""

    # pylint: disable=too-few-public-methods
    __slots__ = ("config", "save_config_to", "version", "verbose")

    config: list[pathlib.Path]
    save_config_to: pathlib.Path | None
    version: bool
    verbose: int


class AwaitableValue[T](Awaitable[T]):
    # pylint: disable=too-few-public-methods
    """An awaitable that always returns the same value."""

    def __await__(self) -> Generator[None, None, T]:
        """Return the value."""
        yield
        return self._value

    def __init__(self, value: T) -> None:
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


class Timer:
    """Timer class used for timing stuff."""

    __slots__ = ("_execution_time", "_start_time")

    _execution_time: int

    def __init__(self) -> None:
        """Start the timer."""
        self._start_time = time.perf_counter_ns()

    def get(self) -> float:
        """Get the execution time in seconds."""
        return self.get_ns() / 1_000_000_000

    def get_ns(self) -> int:
        """Get the execution time in nanoseconds."""
        assert hasattr(self, "_execution_time"), "Timer not stopped yet"
        return self._execution_time

    def stop(self) -> float:
        """Stop the timer and get the execution time in seconds."""
        return self.stop_ns() / 1_000_000_000

    def stop_ns(self) -> int:
        """Stop the timer and get the execution time in nanoseconds."""
        assert not hasattr(self, "_execution_time"), "Timer already stopped"
        self._execution_time = time.perf_counter_ns() - self._start_time
        return self._execution_time


@cache
def add_args_to_url(url: str | SplitResult, **kwargs: object) -> str:
    """Add query arguments to a URL."""
    if isinstance(url, str):
        url = urlsplit(url)

    if not kwargs:
        return url.geturl()

    url_args: dict[str, str] = dict(
        parse_qsl(url.query, keep_blank_values=True)
    )

    for key, value in kwargs.items():
        if value is None:
            if key in url_args:
                del url_args[key]
        # pylint: disable-next=confusing-consecutive-elif
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


def anonymize_ip[  # noqa: D103
    A: (str, None, str | None)
](address: A, *, ignore_invalid: bool = False) -> A:
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


ansi_replace = partial(regex.sub, "\033" + r"\[-?\d+[a-zA-Z]", "")
ansi_replace.__doc__ = "Remove ANSI escape sequences from a string."


def apm_anonymization_processor(
    # pylint: disable-next=unused-argument
    client: elasticapm.Client,
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


def apply[V, Ret](value: V, fun: Callable[[V], Ret]) -> Ret:  # noqa: D103
    """Apply a function to a value and return the result."""
    return fun(value)


backspace_replace = partial(regex.sub, ".?\x08", "")
backspace_replace.__doc__ = "Remove backspaces from a string."


def bool_to_str(val: bool) -> str:
    """Convert a boolean to sure/nope."""
    return "sure" if val else "nope"


def bounded_edit_distance(s1: str, s2: str, /, k: int) -> int:
    """Return a bounded edit distance between two strings.

    k is the maximum number returned
    """
    if (dist := distance(s1, s2, score_cutoff=k)) == k + 1:
        return k
    return dist


def country_code_to_flag(code: str) -> str:
    """Convert a two-letter ISO country code to a flag emoji."""
    return "".join(chr(ord(char) + 23 * 29 * 191) for char in code.upper())


def create_argument_parser() -> argparse.ArgumentParser:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        help="show the version of the website",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--verbose",
        action="count",
        default=0,
    )
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


def emoji2html(emoji: str) -> str:
    """Convert an emoji to HTML."""
    return f"<img src={emoji2url(emoji)!r} alt={emoji!r} class='emoji'>"


def emoji2url(emoji: str) -> str:
    """Convert an emoji to an URL."""
    if len(emoji) == 2:
        emoji = emoji.removesuffix("\uFE0F")
    code = "-".join(f"{ord(c):04x}" for c in emoji)
    return f"/static/openmoji/svg/{code.upper()}.svg?v={OPENMOJI_VERSION}"


if sys.flags.dev_mode or pytest_is_running():
    __origignal_emoji2url = emoji2url

    def emoji2url(emoji: str) -> str:  # pylint: disable=function-redefined
        """Convert an emoji to an URL."""
        import openmoji_dist  # pylint: disable=import-outside-toplevel
        from emoji import is_emoji  # pylint: disable=import-outside-toplevel

        assert is_emoji(emoji), f"{emoji} needs to be emoji"
        result = __origignal_emoji2url(emoji)
        file = (
            openmoji_dist.get_openmoji_data()
            / result.removeprefix("/static/openmoji/").split("?")[0]
        )
        assert file.is_file(), f"{file} needs to exist"
        return result


EMOJI_MAPPING: Final[Mapping[str, str]] = {
    "⁉": "⁉",
    "‼": "‼",
    "?": "❓",
    "!": "❗",
    "-": "➖",
    "+": "➕",
    "\U0001F51F": "\U0001F51F",
}


def emojify(string: str) -> Iterable[str]:
    """Emojify a given string."""
    non_emojis: list[str] = []
    for ch in (
        replace_umlauts(string)
        .replace("!?", "⁉")
        .replace("!!", "‼")
        .replace("10", "\U0001F51F")
    ):
        emoji: str | None = None
        if ch.isascii():
            if ch.isdigit() or ch in "#*":
                emoji = f"{ch}\uFE0F\u20E3"
            elif ch.isalpha():
                emoji = country_code_to_flag(ch)
        emoji = EMOJI_MAPPING.get(ch, emoji)

        if emoji is None:
            non_emojis.append(ch)
        else:
            if non_emojis:
                yield "".join(non_emojis)
                non_emojis.clear()
            yield emoji

    if non_emojis:
        yield "".join(non_emojis)


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

    # pylint: disable-next=redefined-outer-name
    cache = caches.get(ip, {})
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
                    pipeline={
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
                    docs=[{"_source": {"ip": ip}}],
                    filter_path="docs.doc._source",
                )
            )["docs"][0]["doc"]["_source"].get("geoip", {})
        except (ApiError, TransportError):
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


def get_arguments_without_help() -> tuple[str, ...]:
    """Get arguments without help."""
    return tuple(arg for arg in sys.argv[1:] if arg not in {"-h", "--help"})


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
    word_len = len(word)
    if not word_len:
        if cutoff < 1.0:
            return ()
        return Stream(possibilities).limit(count).collect(tuple)
    result: list[tuple[float, str]] = []
    for possibility in possibilities:
        if max_dist := max(word_len, len(possibility)):
            dist = bounded_edit_distance(
                possibility, word, 1 + int(cutoff * max_dist)
            )
            if (ratio := dist / max_dist) <= cutoff:
                bisect.insort(result, (ratio, possibility))
                if len(result) > count:
                    result.pop(-1)
    # Strip scores for the best count matches
    return tuple(word for score, word in result)


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
        hasher=IP_HASH_SALT["hasher"].copy(),  # type: ignore[attr-defined]
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


def n_from_set[T](set_: Set[T], n: int) -> set[T]:  # noqa: D103
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


def none_to_default[T, D](value: None | T, default: D) -> D | T:  # noqa: D103
    """Like ?? in ECMAScript."""
    return default if value is None else value


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
    if value == "glyf_colr0":
        return "glyf_colr0"
    if value == "glyf_colr1":
        return "glyf_colr1"
    if value in {"i", "img"}:
        return "img"
    if value in {"n", "nope"}:
        return False
    return default


# pylint: disable-next=too-many-arguments
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
    remote_ip = hash_bytes(remote_ip.encode("ASCII"))
    key = f"{redis_prefix}:ratelimit:{remote_ip}"
    if bucket:
        key = f"{key}:{bucket}"

    # see: https://github.com/brandur/redis-cell#usage
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


def size_of_file(file: Traversable) -> int:
    """Calculate the size of a file."""
    if isinstance(file, Path):
        return file.stat().st_size

    with file.open("rb") as data:
        return sum(map(len, data))  # pylint: disable=bad-builtin


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


def strangle(string: str) -> float:
    """Convert a string to an angle."""
    hasher = sha1(string.encode("UTF-8"), usedforsecurity=False)
    return int.from_bytes(hasher.digest()[:2], "little") / (1 << 16) * 360


def time_function[  # noqa: D103
    # pylint: disable-next=invalid-name
    T, **P  # fmt: skip
](function: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> tuple[
    T, float
]:
    """Run the function and return the result and the time it took in seconds."""
    timer = Timer()
    return function(*args, **kwargs), timer.stop()


def time_to_str(spam: float) -> str:
    """Convert the time into a string with second precision."""
    int_time = int(spam)
    div_60 = int(int_time / 60)
    div_60_60 = int(div_60 / 60)

    return (
        f"{int(div_60_60 / 24)}d "
        f"{div_60_60 % 24}h "
        f"{div_60 % 60}min "
        f"{int_time % 60}s"
    )


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
    aliases: tuple[str, ...] | Mapping[str, str] = field(default_factory=tuple)
    required_background_tasks: Collection[BackgroundTask] = field(
        default_factory=frozenset
    )

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
