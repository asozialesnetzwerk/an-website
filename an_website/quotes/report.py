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

"""Report wrong quotes for being correct."""
import dataclasses

from tornado.web import MissingArgumentError

from ..main import LOGGER
from ..utils.data_parsing import parse_args
from ..utils.request_handler import APIRequestHandler
from .utils import (
    AUTHORS_CACHE,
    QUOTES_CACHE,
    Author,
    Quote,
    WrongQuote,
    get_wrong_quote,
)


@dataclasses.dataclass(slots=True)
class QuoteReportArgs:
    """Arguments to the quote-report API."""

    author_id: int | None = None
    quote_id: int | None = None
    reason: str | None = None

    def validate(self) -> None:
        """Validate the arguments."""
        if self.author_id is None and self.quote_id is None:
            raise MissingArgumentError("quote_id")

    def get_quote_url_path(self) -> str:
        """Get the URL that got reported."""
        if self.author_id is None:
            return f"/zitate/info/q/{self.quote_id}"
        if self.quote_id is None:
            return f"/zitate/info/a/{self.author_id}"
        return f"/zitate/{self.quote_id}-{self.quote_id}"

    async def get_quote_object(self) -> Quote | WrongQuote | Author | None:
        """Get the quote object."""
        if self.author_id is not None:
            if self.quote_id is not None:
                return await get_wrong_quote(
                    quote_id=self.quote_id, author_id=self.author_id
                )
            return AUTHORS_CACHE.get(self.author_id)
        if self.quote_id is not None:
            return QUOTES_CACHE.get(self.quote_id)
        return None


class QuoteReportApi(APIRequestHandler):
    """Report wrong quotes."""

    @parse_args(type_=QuoteReportArgs, validation_method="validate")
    async def post(self, *, args: QuoteReportArgs) -> None:
        """Handle POST requests to the author info page."""
        quote_obj = await args.get_quote_object()
        LOGGER.critical(
            "Reported: %s\n" "Reason:   %r\n" "\n" "%r",
            self.fix_url(args.get_quote_url_path()),
            args.reason,
            quote_obj.to_json() if quote_obj else None,
        )
        if self.content_type == "application/json":
            await self.finish("true\n")
        else:
            await self.finish()
