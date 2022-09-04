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

"""The Reporting API™️ of the website."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, ClassVar, Final, cast

import orjson as json
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.helpers import async_bulk
from tornado.web import HTTPError

from .. import EVENT_ELASTICSEARCH, ORJSON_OPTIONS
from ..utils.request_handler import APIRequestHandler
from ..utils.utils import ModuleInfo, Permission

LOGGER: Final = logging.getLogger(__name__)


def get_module_info() -> ModuleInfo:
    """Create and return the ModuleInfo for this module."""
    return ModuleInfo(
        handlers=((r"/api/reports", ReportingAPI),),
        name="Reporting API™️",
        description=(
            "Die Reporting API™️ kann zur Überwachung von "
            "Sicherheits-Verstößen, veralteten API-Aufrufen und mehr "
            "von Seiten des Asozialen Netzwerks genutzt werden.\n"
            "Bei Interesse kontakten Sie bitte das Gürteltier."
        ),
        path="/api/reports",
        hidden=True,
    )


async def get_reports(  # pylint: disable=too-many-arguments
    elasticsearch: AsyncElasticsearch,
    prefix: str,
    domain: None | str = None,
    type_: None | str = None,
    from_: int = 0,
    size: int = 10,
) -> list[dict[str, Any]]:
    """Get the reports from Elasticsearch."""
    query: dict[str, dict[str, list[dict[str, dict[str, Any]]]]]
    query = {"bool": {"filter": [{"range": {"@timestamp": {"gte": "now-1M"}}}]}}
    query["bool"]["must_not"] = [
        {
            "bool": {
                "filter": [
                    {"term": {"type": {"value": "network-error"}}},
                    {"term": {"body.type": {"value": "abandoned"}}},
                ]
            }
        },
        {
            "bool": {
                "filter": [
                    {"term": {"type": {"value": "csp-violation"}}},
                    {"term": {"body.source-file": {"value": "moz-extension"}}},
                ]
            }
        },
    ]
    if domain:
        query["bool"]["filter"].append(
            {
                "simple_query_string": {
                    "query": domain,
                    "fields": ["url.domain"],
                    "flags": "AND|ESCAPE|NOT|OR|PHRASE|PRECEDENCE|WHITESPACE",
                }
            }
        )
    if type_:
        query["bool"]["filter"].append(
            {
                "simple_query_string": {
                    "query": type_,
                    "fields": ["type"],
                    "flags": "AND|ESCAPE|NOT|OR|PHRASE|PRECEDENCE|WHITESPACE",
                }
            }
        )
    reports = await elasticsearch.search(
        index=f"{prefix}-reports",
        sort=[{"@timestamp": {"order": "desc"}}],  # type: ignore[list-item]
        query=query,
        from_=from_,
        size=size,
    )
    return [report["_source"] for report in reports["hits"]["hits"]]


class ReportingAPI(APIRequestHandler):
    """The request handler for the Reporting API™️."""

    POSSIBLE_CONTENT_TYPES: ClassVar[
        tuple[str, ...]
    ] = APIRequestHandler.POSSIBLE_CONTENT_TYPES + ("application/x-ndjson",)

    RATELIMIT_GET_LIMIT: ClassVar[int] = 20
    RATELIMIT_GET_COUNT_PER_PERIOD: ClassVar[int] = 2

    RATELIMIT_POST_LIMIT: ClassVar[int] = 20
    RATELIMIT_POST_COUNT_PER_PERIOD: ClassVar[int] = 2

    MAX_BODY_SIZE: ClassVar[int] = 1_000_000

    MAX_REPORTS_PER_REQUEST: ClassVar[int] = 100

    async def get(self, *, head: bool = False) -> None:  # noqa: C901
        """Handle GET requests to the Reporting API™️."""
        if not EVENT_ELASTICSEARCH.is_set():
            raise HTTPError(503)

        if head:
            return

        domain = self.get_argument("domain", None)
        type_ = self.get_argument("type", None)
        from_ = self.get_int_argument("from", 0, min_=0)
        size = self.get_int_argument("size", 10, min_=0)

        if not self.is_authorized(Permission.REPORTING):
            from_ = 0
            size = min(10, size)

        try:
            reports = await get_reports(
                self.elasticsearch,
                self.elasticsearch_prefix,
                domain,
                type_,
                from_,
                size,
            )
        except NotFoundError:  # data stream doesn't exist
            raise HTTPError(404) from None

        if self.content_type == "application/x-ndjson":
            await self.finish(
                b"\n".join(
                    json.dumps(report, option=ORJSON_OPTIONS)
                    for report in reports
                )
            )
        else:
            await self.finish(self.dump(reports))

    async def post(self) -> None:  # noqa: C901
        """Handle POST requests to the Reporting API™️."""
        # pylint: disable=too-complex, too-many-branches
        if not (
            self.settings.get("REPORTING_BUILTIN")
            and EVENT_ELASTICSEARCH.is_set()
        ):
            raise HTTPError(503)
        if self.request.headers.get("Content-Type", "").startswith(
            "application/reports+json"
        ):
            reports = json.loads(self.request.body)
        elif self.request.headers.get("Content-Type", "").startswith(
            "application/csp-report"
        ):
            data = json.loads(self.request.body)
            if not isinstance(data, dict):
                raise HTTPError(400)
            body = data.get("csp-report")
            if not isinstance(body, dict):
                raise HTTPError(400)
            for camel, kebab in (
                ("blockedURL", "blocked-uri"),
                ("documentURL", "document-uri"),
                ("effectiveDirective", "effective-directive"),
                ("originalPolicy", "original-policy"),
                ("sample", "script-sample"),
                ("statusCode", "status-code"),
                ("violatedDirective", "violated-directive"),
            ):
                if kebab in body:
                    body[camel] = body.pop(kebab)  # 🥙 → 🐪
            report = {
                "age": 0,
                "body": body,
                "type": "csp-violation",
                "url": body.get("documentURL"),
                "user_agent": self.request.headers.get("User-Agent"),
            }
            reports = [report]
        else:
            raise HTTPError(415)
        if not isinstance(reports, list):
            raise HTTPError(400)
        if len(reports) > self.MAX_REPORTS_PER_REQUEST:
            LOGGER.warning(
                "%s > MAX_REPORTS_PER_REQUEST (%s)",
                len(reports),
                self.MAX_REPORTS_PER_REQUEST,
            )
            raise HTTPError(400)
        self.set_status(202)
        self.finish()
        for report in reports.copy():
            if not isinstance(report, dict):
                reports.remove(report)  # type: ignore[unreachable]
                continue
            if isinstance((sauce := report.pop("_source", None)), dict):
                report.update(sauce)
            if not all(
                (
                    isinstance(report.get("age"), int),
                    isinstance(report.get("body"), dict),
                    isinstance(report.get("type"), str),
                    isinstance(report.get("url"), str),
                    isinstance(report.get("user_agent"), str),
                )
            ):
                reports.remove(report)
                continue
            report["@timestamp"] = self.now - timedelta(
                milliseconds=max(0, cast(int, report.pop("age")))
            )
            report["ecs"] = {"version": "1.12.2"}
            report["_op_type"] = "create"
            report.pop("_index", None)  # DO NOT REMOVE
        await async_bulk(
            self.elasticsearch,
            reports,
            index=f"{self.elasticsearch_prefix}-reports",
        )
