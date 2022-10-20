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

"""The dataclass representing a quote of the day."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone  # noqa: F401
from email.utils import format_datetime
from typing import Any

from ..utils import WrongQuote


@dataclass(slots=True)
class QuoteOfTheDayData:
    """The class representing data for the quote of the day."""

    date: date
    wrong_quote: WrongQuote
    url_without_path: str

    def get_date_for_rss(self) -> str:
        """Get the date as specified in RFC 2822."""
        return format_datetime(
            datetime(
                year=self.date.year,
                month=self.date.month,
                day=self.date.day,
                tzinfo=timezone.utc,
            ),
            True,
        )

    def get_quote_as_str(self, new_line_char: str = "\n") -> str:
        """Get the quote as a string with new line."""
        return (
            f"»{self.wrong_quote.quote}«{new_line_char}"
            f"- {self.wrong_quote.author}"
        )

    def get_quote_image_url(self) -> str:
        """Get the URL of the image of the quote."""
        return self.get_quote_url() + ".gif"

    def get_quote_url(self) -> str:
        """Get the URL of the quote."""
        return (
            f"{self.url_without_path}/zitate/{self.wrong_quote.get_id_as_str()}"
        )

    def get_title(self) -> str:
        """Get the title for the quote of the day."""
        return f"Das Zitat des Tages vom {self.date:%d. %m. %Y}"

    def to_json(self) -> dict[str, str | dict[str, Any]]:
        """Get the quote of the day as JSON."""
        return {
            "date": self.date.isoformat(),
            "wrong_quote": self.wrong_quote.to_json(),
            "url": self.get_quote_url(),
            "image": self.get_quote_image_url(),
        }
