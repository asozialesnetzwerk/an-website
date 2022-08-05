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

"""
Useful request handlers used by other modules.

This should only contain request handlers and the get_module_info function.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from asyncio import Future
from datetime import date, datetime, timedelta
from http.client import responses
from typing import Any
from urllib.parse import unquote, urlsplit

import html2text
import regex
from ansi2html import Ansi2HTMLConverter
from bs4 import BeautifulSoup
from dateutil.easter import easter
from sympy.ntheory import isprime
from tornado.httpclient import AsyncHTTPClient
from tornado.web import HTTPError

from .. import DIR as ROOT_DIR
from .. import GH_ORG_URL, GH_PAGES_URL, GH_REPO_URL
from .base_request_handler import BaseRequestHandler
from .static_file_handling import fix_static_url
from .utils import (
    SUS_PATHS,
    ModuleInfo,
    Permission,
    bool_to_str,
    create_emoji_html,
    emoji2code,
    normalized_levenshtein,
    remove_suffix_ignore_case,
    replace_umlauts,
    str_to_bool,
)

logger = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        name="Utilities",
        description="Nützliche Werkzeuge für alle möglichen Sachen.",
        handlers=(
            (
                r"/error",
                ZeroDivision if sys.flags.dev_mode else NotFoundHandler,
                {},
            ),
            (r"/([1-5][0-9]{2}).html?", ErrorPage, {}),
            (
                r"/@elastic/apm-rum@(.+)/dist/bundles"
                r"/elastic-apm-rum.umd(\.min|).js(\.map|)",
                ElasticRUM,
            ),
        ),
        hidden=True,
    )


class HTMLRequestHandler(BaseRequestHandler):
    """A request handler that serves HTML."""

    POSSIBLE_CONTENT_TYPES: tuple[str, ...] = (
        "text/html",
        "text/plain",
        "text/markdown",
        "application/json",
    )
    used_render = False

    def finish(
        self, chunk: None | str | bytes | dict[Any, Any] = None
    ) -> Future[None]:
        """Finish the request."""
        as_json: bool = self.content_type == "application/json"
        as_plain_text: bool = self.content_type == "text/plain"
        as_markdown: bool = self.content_type == "text/markdown"
        if (
            not isinstance(chunk, bytes | str)
            or not self.used_render
            or getattr(self, "IS_NOT_HTML", False)
            or not (as_json or as_plain_text or as_markdown)
        ):
            return super().finish(chunk)

        chunk = chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk

        if as_markdown:
            return super().finish(
                f"# {self.title}\n\n"
                + html2text.html2text(chunk, self.request.full_url()).strip()
            )

        soup = BeautifulSoup(chunk, features="lxml")
        if as_plain_text:
            return super().finish(soup.get_text("\n", True))

        dictionary: dict[str, Any] = dict(
            url=self.fix_url(),  # request url
            title=self.title,
            short_title=self.short_title
            if self.title != self.short_title
            else None,
            body="".join(
                str(_el)
                for _el in soup.find_all(name="main", id="body")[0].contents
            ).strip(),
            scripts=[
                {
                    "src": _s.get("src"),
                    # "script": _s.string,  # not in use because of csp
                    # "onload": _s.get("onload"),  # not in use because of csp
                }
                for _s in soup.find_all("script")
            ]
            if soup.head
            else [],
            stylesheets=[
                str(_s.get("href")).strip()
                for _s in soup.find_all("link", rel="stylesheet")
            ]
            if soup.head
            else [],
            css="\n".join(str(_s.string or "") for _s in soup.find_all("style"))
            if soup.head
            else "",
        )
        return super().finish(dictionary)

    def get_form_appendix(self) -> str:
        """Get HTML to add to forms to keep important query args."""
        form_appendix = (
            "<input name='no_3rd_party' class='hidden' "
            f"value='{bool_to_str(self.get_no_3rd_party())}'>"
            if "no_3rd_party" in self.request.query_arguments
            and self.get_no_3rd_party() != self.get_saved_no_3rd_party()
            else ""
        )
        if self.get_dynload() != self.get_saved_dynload():
            form_appendix += (
                "<input name='dynload' class='hidden' "
                f"value='{bool_to_str(self.get_dynload())}'>"
            )
        if (theme := self.get_theme()) != self.get_saved_theme():
            form_appendix += (
                f"<input name='theme' class='hidden' value='{theme}'>"
            )
        return form_appendix

    def get_template_namespace(self) -> dict[str, Any]:
        """
        Add useful things to the template namespace and return it.

        They are mostly needed by most of the pages (like title,
        description and no_3rd_party).
        """
        namespace = super().get_template_namespace()
        namespace.update(
            ansi2html=Ansi2HTMLConverter(inline=True, scheme="xterm"),
            as_html=self.content_type == "text/html",
            c=self.settings.get("TESTING")
            or self.now.date() == date(self.now.year, 4, 1)
            or str_to_bool(self.get_cookie("c", "f") or "f", False),
            canonical_url=self.fix_url(
                self.request.full_url().upper()
                if self.request.path.upper().startswith("/LOLWUT")
                else self.request.full_url().lower()
            ).split("?")[0],
            description=self.description,
            dynload=self.get_dynload(),
            elastic_rum_url=self.ELASTIC_RUM_URL,
            fix_static=lambda url: self.fix_url(fix_static_url(url)),
            fix_url=self.fix_url,
            openmoji=self.get_openmoji(),
            emoji2html=(
                lambda emoji: create_emoji_html(
                    emoji,
                    self.fix_url(
                        fix_static_url(
                            f"img/openmoji-svg-14.0/{emoji2code(emoji)}.svg"
                        )
                    ),
                )
            )
            if self.get_openmoji() == "img"
            else lambda spam: spam,  # type: ignore[no-any-return]
            form_appendix=self.get_form_appendix(),
            GH_ORG_URL=GH_ORG_URL,
            GH_PAGES_URL=GH_PAGES_URL,
            GH_REPO_URL=GH_REPO_URL,
            keywords="Asoziales Netzwerk, Känguru-Chroniken"
            + (
                f", {self.module_info.get_keywords_as_str(self.request.path)}"
                if self.module_info
                else ""
            ),
            lang="de",  # TODO: add language support
            no_3rd_party=self.get_no_3rd_party(),
            now=self.now,
            settings=self.settings,
            short_title=self.short_title,
            theme=self.get_display_theme(),
            title=self.title,
            apm_script=self.settings["ELASTIC_APM"].get("INLINE_SCRIPT")
            if self.apm_enabled
            else None,
        )
        namespace.update(
            {
                "🥚": self.settings.get("TESTING")
                or timedelta()
                <= self.now.date() - easter(self.now.year)
                < timedelta(days=2),
                "🦘": self.settings.get("TESTING")
                or isprime(self.now.microsecond),  # type: ignore[no-untyped-call]
            }
        )
        return namespace

    def render(self, template_name: str, **kwargs: Any) -> Future[None]:
        """Render a template."""
        self.used_render = True
        return super().render(template_name, **kwargs)

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        """Render the error page with the status_code as a HTML page."""
        self.render(
            "error.html",
            status=status_code,
            reason=self.get_error_message(**kwargs),
            description=self.get_error_page_description(status_code),
            is_traceback="exc_info" in kwargs
            and not issubclass(kwargs["exc_info"][0], HTTPError)
            and (
                self.settings.get("serve_traceback")
                or self.is_authorized(Permission.TRACEBACK)
            ),
        )


class APIRequestHandler(BaseRequestHandler):
    """
    The base API request handler.

    It overrides the write error method to return errors as JSON.
    """

    POSSIBLE_CONTENT_TYPES: tuple[str, ...] = (
        "application/json",
        "application/yaml",
    )
    IS_NOT_HTML = True

    def finish_dict(self, **kwargs: Any) -> Future[None]:
        """Finish the request with a JSON response."""
        return self.finish(kwargs)

    def write_error(self, status_code: int, **kwargs: dict[str, Any]) -> None:
        """Finish with the status code and the reason as dict."""
        self.finish_dict(
            status=status_code,
            reason=self.get_error_message(**kwargs),
        )


class NotFoundHandler(HTMLRequestHandler):
    """Show a 404 page if no other RequestHandler is used."""

    def initialize(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing to have default title and description."""
        if "module_info" not in kwargs:
            kwargs["module_info"] = None
        super().initialize(*args, **kwargs)

    async def prepare(self) -> None:  # pylint: disable=too-complex # noqa: C901
        """Throw a 404 HTTP error or redirect to another page."""
        self.now = await self.get_time()

        self.handle_accept_header(self.POSSIBLE_CONTENT_TYPES)

        if self.request.method not in {"GET", "HEAD"}:
            raise HTTPError(404)
        new_path = regex.sub(r"/+", "/", self.request.path.rstrip("/")).replace(
            "_", "-"
        )
        for ext in (".html", ".htm", ".php"):
            new_path = remove_suffix_ignore_case(new_path, f"/index{ext}")
            new_path = remove_suffix_ignore_case(new_path, ext)

        new_path = replace_umlauts(new_path)

        if new_path.lower() in SUS_PATHS:
            self.set_status(469, reason="Nice Try")
            return self.write_error(469)

        if new_path != self.request.path:
            return self.redirect(self.fix_url(new_path=new_path), True)

        this_path_normalized = unquote(new_path).strip("/").lower()

        if len(this_path_normalized) == 1:
            return self.redirect(self.fix_url(new_path="/"))

        distances: list[tuple[float, str]] = []
        max_dist = 0.5

        for module_info in self.get_module_infos():
            if module_info.path is not None:
                dist = min(  # get the smallest distance with the aliases
                    normalized_levenshtein(
                        this_path_normalized, path.strip("/").lower()
                    )
                    for path in (*module_info.aliases, module_info.path)
                    if path != "/z"  # do not redirect to /z
                )
                if dist <= max_dist:
                    # only if the distance is less than or equal {max_dist}
                    distances.append((dist, module_info.path))
            if len(module_info.sub_pages) > 0:
                distances.extend(
                    (
                        normalized_levenshtein(
                            this_path_normalized,
                            sub_page.path.strip("/").lower(),
                        ),
                        sub_page.path,
                    )
                    for sub_page in module_info.sub_pages
                    if sub_page.path is not None
                )

        if len(distances) > 0:
            # sort to get the one with the smallest distance in index 0
            distances.sort()
            dist, path = distances[0]
            # redirect only if the distance is less than or equal {max_dist}
            if dist <= max_dist:
                return self.redirect(self.fix_url(new_path=path), False)

        self.set_status(404)
        self.write_error(404)


class ErrorPage(HTMLRequestHandler):
    """A request handler that shows the error page."""

    async def get(self, code: str) -> None:
        """Show the error page."""
        status_code = int(code)
        reason = (
            "Nice Try" if status_code == 469 else responses.get(status_code, "")
        )
        # set the status code if it is allowed
        if status_code not in (204, 304) and not 100 <= status_code < 200:
            self.set_status(status_code, reason)
        return await self.render(
            "error.html",
            status=status_code,
            reason=reason,
            description=self.get_error_page_description(status_code),
            is_traceback=False,
        )


class ZeroDivision(HTMLRequestHandler):
    """A request handler that raises an error."""

    async def prepare(self) -> None:
        """Divide by zero and raise an error."""
        self.now = await self.get_time()
        self.handle_accept_header(self.POSSIBLE_CONTENT_TYPES)
        if self.request.method != "OPTIONS":
            420 / 0  # pylint: disable=pointless-statement


class ElasticRUM(BaseRequestHandler):
    """A request handler that serves the Elastic RUM Agent."""

    POSSIBLE_CONTENT_TYPES: tuple[str, ...] = (
        "application/javascript",
        "application/json",
    )

    URL = (
        "https://unpkg.com/@elastic/apm-rum@{}"
        "/dist/bundles/elastic-apm-rum.umd{}.js{}"
    )

    SCRIPTS: dict[str, tuple[str, float]] = {}
    CACHE_TIME = 365 * 60 * 60 * 24

    async def get(
        self,
        version: str,
        spam: str = "",
        eggs: str = "",
        *,
        # pylint: disable=unused-argument
        head: bool = False,
    ) -> None:
        """Serve the RUM script."""
        accepted_ct = "application/json" if eggs else "application/javascript"
        self.handle_accept_header((accepted_ct,))

        key = version + spam + eggs
        if key not in self.SCRIPTS or self.SCRIPTS[key][1] < time.monotonic():
            response = await AsyncHTTPClient().fetch(
                self.URL.format(version, spam, eggs),
                raise_error=False,
                ca_certs=os.path.join(ROOT_DIR, "ca-bundle.crt"),
            )
            if response.code != 200:
                raise HTTPError(response.code, reason=response.reason)
            self.SCRIPTS[key] = (
                response.body.decode(),
                time.monotonic() + 365 * 24 * 60 * 60,
            )
            new_path = urlsplit(response.effective_url).path
            if new_path.endswith(".js"):
                BaseRequestHandler.ELASTIC_RUM_URL = new_path
            logger.info("RUM script %s updated", new_path)
            self.redirect(self.fix_url(new_path), False)
            return
        if spam and not eggs:  # if serving minified JS (URL contains ".min")
            self.set_header(
                "SourceMap", self.request.full_url().split("?")[0] + ".map"
            )
        self.set_header(
            "Expires", datetime.utcnow() + timedelta(seconds=self.CACHE_TIME)
        )
        self.set_header(
            "Cache-Control", f"public, min-fresh={self.CACHE_TIME}, immutable"
        )
        return await self.finish(self.SCRIPTS[key][0])
