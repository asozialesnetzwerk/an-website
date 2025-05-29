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
"""Functions for setting up Elasticsearch."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Final, Literal, TypeAlias, TypedDict, cast

import orjson
from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch, NotFoundError
from tornado.web import Application

from .. import CA_BUNDLE_PATH, DIR
from .better_config_parser import BetterConfigParser
from .fix_static_path_impl import recurse_directory
from .utils import none_to_default

LOGGER: Final = logging.getLogger(__name__)

ES_WHAT_LITERAL: TypeAlias = Literal[  # pylint: disable=invalid-name
    "component_templates", "index_templates", "ingest_pipelines"
]
ES_WHAT_LITERALS: tuple[ES_WHAT_LITERAL, ...] = (
    "ingest_pipelines",
    "component_templates",
    "index_templates",
)
type AnyArgsAsyncMethod = Callable[..., Awaitable[ObjectApiResponse[object]]]


async def setup_elasticsearch_configs(
    elasticsearch: AsyncElasticsearch,
    prefix: str,
) -> None:
    """Setup Elasticsearch configs."""  # noqa: D401
    spam: list[Awaitable[None | ObjectApiResponse[object]]]

    for i in range(3):
        spam = []

        what: ES_WHAT_LITERAL = ES_WHAT_LITERALS[i]

        base_path = DIR / "elasticsearch" / what

        for rel_path in recurse_directory(
            base_path, lambda path: path.name.endswith(".json")
        ):
            path = base_path / rel_path
            if not path.is_file():
                LOGGER.warning("%s is not a file", path)
                continue

            body = orjson.loads(
                path.read_bytes().replace(b"{prefix}", prefix.encode("ASCII"))
            )

            name = f"{prefix}-{rel_path[:-5].replace('/', '-')}"

            spam.append(
                setup_elasticsearch_config(
                    elasticsearch, what, body, name, rel_path
                )
            )

        await asyncio.gather(*spam)


async def setup_elasticsearch_config(
    es: AsyncElasticsearch,
    what: ES_WHAT_LITERAL,
    body: dict[str, object],
    name: str,
    path: str = "<unknown>",
) -> None | ObjectApiResponse[object]:
    """Setup Elasticsearch config."""  # noqa: D401
    if what == "component_templates":
        get: AnyArgsAsyncMethod = es.cluster.get_component_template
        put: AnyArgsAsyncMethod = es.cluster.put_component_template
    elif what == "index_templates":
        get = es.indices.get_index_template
        put = es.indices.put_index_template
    elif what == "ingest_pipelines":
        get = es.ingest.get_pipeline
        put = es.ingest.put_pipeline
    else:
        raise AssertionError()

    try:
        if what == "ingest_pipelines":
            current = await get(id=name)
            current_version = current[name].get("version", 1)
        else:
            current = await get(
                name=name, filter_path=f"{what}.name,{what}.version"
            )
            current_version = current[what][0].get("version", 1)
    except NotFoundError:
        current_version = 0

    if current_version < body.get("version", 1):
        if what == "ingest_pipelines":
            return await put(id=name, body=body)
        return await put(name=name, body=body)

    if current_version > body.get("version", 1):
        LOGGER.warning(
            "%s has version %s. The version in Elasticsearch is %s!",
            path,
            body.get("version", 1),
            current_version,
        )

    return None


def setup_elasticsearch(app: Application) -> None | AsyncElasticsearch:
    """Setup Elasticsearch."""  # noqa: D401
    # pylint: disable-next=import-outside-toplevel
    from elastic_transport.client_utils import DEFAULT, DefaultType

    config: BetterConfigParser = app.settings["CONFIG"]
    basic_auth: tuple[str | None, str | None] = (
        config.get("ELASTICSEARCH", "USERNAME", fallback=None),
        config.get("ELASTICSEARCH", "PASSWORD", fallback=None),
    )

    class Kwargs(TypedDict):
        """Kwargs of AsyncElasticsearch constructor."""

        hosts: tuple[str, ...] | None
        cloud_id: None | str
        verify_certs: bool
        api_key: None | str
        bearer_auth: None | str
        client_cert: str | DefaultType
        client_key: str | DefaultType
        retry_on_timeout: bool | DefaultType

    kwargs: Kwargs = {
        "hosts": (
            tuple(config.getset("ELASTICSEARCH", "HOSTS"))
            if config.has_option("ELASTICSEARCH", "HOSTS")
            else None
        ),
        "cloud_id": config.get("ELASTICSEARCH", "CLOUD_ID", fallback=None),
        "verify_certs": config.getboolean(
            "ELASTICSEARCH", "VERIFY_CERTS", fallback=True
        ),
        "api_key": config.get("ELASTICSEARCH", "API_KEY", fallback=None),
        "bearer_auth": config.get(
            "ELASTICSEARCH", "BEARER_AUTH", fallback=None
        ),
        "client_cert": none_to_default(
            config.get("ELASTICSEARCH", "CLIENT_CERT", fallback=None), DEFAULT
        ),
        "client_key": none_to_default(
            config.get("ELASTICSEARCH", "CLIENT_KEY", fallback=None), DEFAULT
        ),
        "retry_on_timeout": none_to_default(
            config.getboolean(
                "ELASTICSEARCH", "RETRY_ON_TIMEOUT", fallback=None
            ),
            DEFAULT,
        ),
    }
    if not config.getboolean("ELASTICSEARCH", "ENABLED", fallback=False):
        app.settings["ELASTICSEARCH"] = None
        return None
    elasticsearch = AsyncElasticsearch(
        basic_auth=(
            None if None in basic_auth else cast(tuple[str, str], basic_auth)
        ),
        ca_certs=CA_BUNDLE_PATH,
        **kwargs,
    )
    app.settings["ELASTICSEARCH"] = elasticsearch
    return elasticsearch
