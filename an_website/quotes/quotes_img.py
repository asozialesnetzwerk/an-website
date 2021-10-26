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

"""Module that generates an image from a wrong quote."""
from __future__ import annotations

import io
import textwrap

from PIL import Image, ImageDraw, ImageFont

from . import (
    DIR,
    QuoteReadyCheckRequestHandler,
    get_author_by_id,
    get_quote_by_id,
)

AUTHOR_MAX_WIDTH: int = 686
QUOTE_MAX_WIDTH: int = 900
TEXT_COLOR: tuple[int, int, int] = 230, 230, 230
FONT = ImageFont.truetype(
    font=f"{DIR}/files/libre-sans-serif-ssi.ttf",
    size=50,
)

BG_IMG = Image.open(f"{DIR}/files/bg.png")
IMAGE_HEIGHT: int = BG_IMG.size[1]


def get_lines_and_max_height(
    text: str, max_width: int
) -> tuple[list[str], int]:
    """Get the lines of the text and the max line height."""
    column_count = 42
    lines: list[str] = []

    max_line_length = max_width + 1
    while max_line_length > max_width:
        lines = textwrap.wrap(text, width=column_count)
        max_line_length = max(FONT.getsize(line)[0] for line in lines)
        column_count -= 1

    return lines, max(FONT.getsize(line)[1] for line in lines)


def draw_lines(
    img: ImageDraw.ImageDraw,
    lines: list[str],
    y_start: int,
    max_w: int,
    max_h: int,
) -> int:
    """Draw the lines on the image and return the last y position."""
    for line in lines:
        width = FONT.getsize(line)[0]
        img.text(
            (
                (max_w - width) / 2,
                y_start,
            ),
            line,
            font=FONT,
            fill=TEXT_COLOR,
            align="right",
            spacing=54,
        )
        y_start += max_h
    return y_start


def create_image(quote: str, author: str):
    """Create an image with the given quote and author."""
    img = BG_IMG.copy()
    draw = ImageDraw.Draw(img, mode="RGBA")

    quote_lines, max_line_height = get_lines_and_max_height(
        f"»{quote}«", QUOTE_MAX_WIDTH
    )
    y_text = draw_lines(
        draw,
        quote_lines,
        50,
        QUOTE_MAX_WIDTH,
        max_line_height,
    )

    author = f"- {author}"
    width, max_line_height = FONT.getsize(author)
    if width <= AUTHOR_MAX_WIDTH:
        author_lines = [author]
    else:
        author_lines, max_line_height = get_lines_and_max_height(
            author, AUTHOR_MAX_WIDTH
        )
    draw_lines(
        draw,
        author_lines,
        max(y_text + 20, IMAGE_HEIGHT - 220),
        AUTHOR_MAX_WIDTH,
        max_line_height,
    )

    io_buf = io.BytesIO()
    img.save(
        io_buf,
        format="PNG",
    )
    return io_buf.getvalue()


class QuoteAsImg(QuoteReadyCheckRequestHandler):
    """Quote as img request handler."""

    RATELIMIT_TOKENS = 5

    async def get(self, quote_id: str, author_id: str):
        """Handle the get request to this page and render the quote as img."""
        self.set_header("Content-Type", "image/png")
        await self.finish(
            create_image(
                (await get_quote_by_id(int(quote_id))).quote,
                (await get_author_by_id(int(author_id))).name,
            )
        )