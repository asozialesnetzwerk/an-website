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
"""Async elasticsearch."""

import logging
from typing import Final

from elastic_transport import (
    ApiResponse,
    ApiResponseMeta,
    BaseAsyncNode,
    HttpHeaders,
    NodeConfig,
)
from elastic_transport.client_utils import DefaultType
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

LOGGER: Final = logging.getLogger(__name__)


class TornadoAsyncNode(BaseAsyncNode):
    """A node that performs requests."""

    __client: AsyncHTTPClient | None

    def __init__(self, config: NodeConfig) -> None:
        """Initialise self."""
        super().__init__(config)
        self.__client = None

    @property
    def _client(self) -> AsyncHTTPClient:
        """Get the AsyncHTTPClient."""
        if self.__client is None:
            self.__client = AsyncHTTPClient(
                force_instance=True,
                defaults={
                    "ca_certs": self.config.ca_certs,
                    "client_cert": self.config.client_cert,
                    "client_key": self.config.client_key,
                    "ssl_options": self.config.ssl_context,
                    "use_gzip": self._http_compress,
                    "validate_cert": self.config.verify_certs,
                },
            )
        return self.__client

    async def close(self) -> None:  # type: ignore[override]
        """Close the connection."""
        if self.__client:
            self.__client.close()
            self.__client = None

    # pylint: disable-next=too-many-arguments
    async def perform_request(  # type: ignore[override]
        self,
        method: str,
        target: str,
        body: bytes | None = None,
        headers: HttpHeaders | None = None,
        request_timeout: float | DefaultType | None = None,
    ) -> ApiResponse[bytes]:
        """Perform a request."""
        if isinstance(request_timeout, DefaultType):
            request_timeout = None
        url = self.base_url + target

        request = HTTPRequest(
            url=url,
            method=method,
            body=body,
            headers={
                **self._headers,
                **(headers or {}),
            },
            request_timeout=request_timeout,
        )

        response = await self._client.fetch(
            request,
            raise_error=False,
        )

        LOGGER.debug(
            "%s %s [status:%s duration:%fs]",
            method,
            url,
            response.code,
            response.request_time,
        )

        return ApiResponse(
            meta=ApiResponseMeta(
                status=response.code,
                duration=(
                    -1.0
                    if response.request_time is None
                    else response.request_time
                ),
                headers=HttpHeaders(response.headers),
                node=self._config,
                http_version="1.1",
            ),
            body=response.body,
        )
