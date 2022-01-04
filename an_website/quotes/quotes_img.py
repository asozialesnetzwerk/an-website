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
import logging
import math
import textwrap

from jxlpy import (  # type: ignore  # noqa  # pylint: disable=W0611
    JXLImagePlugin,
)
from PIL import Image, ImageDraw, ImageFont
from tornado.web import HTTPError

from ..utils.utils import str_to_bool
from . import DIR, QuoteReadyCheckRequestHandler, get_wrong_quote

logger = logging.getLogger(__name__)

AUTHOR_MAX_WIDTH: int = 686
QUOTE_MAX_WIDTH: int = 900
TEXT_COLOR: tuple[int, int, int] = 230, 230, 230
FONT = ImageFont.truetype(
    font=f"{DIR}/files/oswald.regular.ttf",
    size=50,
)
FONT_SMALLER = ImageFont.truetype(
    font=f"{DIR}/files/oswald.regular.ttf",
    size=44,
)
HOST_NAME_FONT = ImageFont.truetype(
    font=f"{DIR}/files/oswald.regular.ttf",
    size=23,
)


def load_png(file_name: str) -> Image.Image:
    """Load a png into memory."""
    img = Image.open(f"{DIR}/files/{file_name}.png", formats=("PNG",))
    img_copy = img.copy()
    img.close()
    return img_copy


BG_IMG = load_png("bg")
IMAGE_WIDTH, IMAGE_HEIGHT = BG_IMG.size
WITZIG_IMG = load_png("StempelWitzig")
NICHT_WITZIG_IMG = load_png("StempelNichtWitzig")


def get_lines_and_max_height(
    text: str,
    max_width: int,
    font: ImageFont.FreeTypeFont,
) -> tuple[list[str], int]:
    """Get the lines of the text and the max line height."""
    column_count = 46
    lines: list[str] = []

    max_line_length = max_width + 1
    while max_line_length > max_width:  # pylint: disable=while-used
        lines = textwrap.wrap(text, width=column_count)
        max_line_length = max(font.getsize(line)[0] for line in lines)
        column_count -= 1

    return lines, max(font.getsize(line)[1] for line in lines)


def draw_text(
    img: ImageDraw.ImageDraw,
    text: str,
    _x: int,
    _y: int,
    font: ImageFont.FreeTypeFont,
) -> None:
    """Draw a text on an image."""
    img.text(
        (_x, _y),
        text,
        font=font,
        fill=TEXT_COLOR,
        align="right",
        spacing=54,
    )


def draw_lines(  # pylint: disable=too-many-arguments
    img: ImageDraw.ImageDraw,
    lines: list[str],
    y_start: int,
    max_w: int,
    max_h: int,
    font: ImageFont.FreeTypeFont,
    padding_left: int = 0,
) -> int:
    """Draw the lines on the image and return the last y position."""
    for line in lines:
        width = font.getsize(line)[0]
        draw_text(
            img=img,
            text=line,
            _x=padding_left + math.ceil((max_w - width) / 2),
            _y=y_start,
            font=font,
        )
        y_start += max_h
    return y_start


def create_image(  # pylint: disable=R0912, R0913, R0914, R0915  # noqa: C901
    quote: str,
    author: str,
    rating: int,
    source: None | str,
    file_type: str = "png",
    font: ImageFont.FreeTypeFont = FONT,
) -> bytes:
    """Create an image with the given quote and author."""
    img = BG_IMG.copy()
    draw = ImageDraw.Draw(img, mode="RGBA")

    # draw quote
    quote_str = f"»{quote}«"
    width, max_line_height = font.getsize(quote_str)
    if width <= AUTHOR_MAX_WIDTH:
        quote_lines = [quote_str]
    else:
        quote_lines, max_line_height = get_lines_and_max_height(
            quote_str, QUOTE_MAX_WIDTH, font
        )
    if len(quote_lines) < 3:
        y_start = 175
    elif len(quote_lines) < 4:
        y_start = 125
    elif len(quote_lines) < 6:
        y_start = 75
    else:
        y_start = 50
    y_text = draw_lines(
        draw,
        quote_lines,
        y_start,
        QUOTE_MAX_WIDTH,
        max_line_height,
        font,
    )

    # draw author
    author_str = f"- {author}"
    width, max_line_height = font.getsize(author_str)
    if width <= AUTHOR_MAX_WIDTH:
        author_lines = [author_str]
    else:
        author_lines, max_line_height = get_lines_and_max_height(
            author_str, AUTHOR_MAX_WIDTH, font
        )
    y_text = draw_lines(
        draw,
        author_lines,
        max(
            y_text + 20, IMAGE_HEIGHT - (220 if len(author_lines) < 3 else 280)
        ),
        AUTHOR_MAX_WIDTH,
        max_line_height,
        font,
        10,
    )

    if y_text > IMAGE_HEIGHT and font is FONT:
        logger.info("Using smaller font for quote %s", source)
        return create_image(
            quote=quote,
            author=author,
            rating=rating,
            source=source,
            file_type=file_type,
            font=FONT_SMALLER,
        )

    # draw rating
    if rating:
        width, height = FONT_SMALLER.getsize(str(rating))
        y_rating = IMAGE_HEIGHT - 25 - height
        draw_text(
            img=draw,
            text=str(rating),
            _x=25,
            _y=y_rating,
            font=FONT_SMALLER,  # always use same font for rating
        )
        # draw rating img
        icon = NICHT_WITZIG_IMG if rating < 0 else WITZIG_IMG
        img.paste(
            icon,
            box=(
                25 + 5 + width,
                y_rating + 8,  # 8 is a magic number 🧝
            ),
            mask=icon,
        )

    # draw host name
    if source is not None:
        width, height = HOST_NAME_FONT.getsize(source)
        draw_text(
            img=draw,
            text=source,
            _x=IMAGE_WIDTH - 5 - width,
            _y=IMAGE_HEIGHT - 5 - height,
            font=HOST_NAME_FONT,
        )

    io_buf = io.BytesIO()
    kwargs = {
        "format": file_type,
        "optimize": True,
        "save_all": False,
    }
    if file_type == "4-color-gif":
        colors: list[tuple[int, tuple[int, int, int]]] = img.getcolors(  # type: ignore
            9999
        )
        colors.sort(reverse=True)
        _vals: list[int] = []
        for _, _c in colors[:4]:
            _vals.extend(_c)
        kwargs.update(format="gif", palette=bytearray(_vals))
    elif file_type == "webp":
        kwargs.update(lossless=True)
    elif file_type == "tiff":
        kwargs.update(compression="zlib")
    elif file_type == "jxl":
        kwargs.update(lossless=True, effort=7)
    img.save(io_buf, **kwargs)  # type: ignore
    return io_buf.getvalue()


FILE_EXTENSIONS = {
    "png": "png",
    "gif": "gif",
    "jpeg": "jpeg",
    "jpg": "jpeg",
    "jfif": "jpeg",
    "jpe": "jpeg",
    "jxl": "jxl",
    "webp": "webp",
    "bmp": "bmp",
    "pdf": "pdf",
    "spi": "spider",
    "tiff": "tiff",
}


class QuoteAsImg(QuoteReadyCheckRequestHandler):
    """Quote as img request handler."""

    RATELIMIT_NAME = "quotes-img"

    RATELIMIT_TOKENS = 4

    async def get(
        self, quote_id: str, author_id: str, file_extension: str = "png"
    ) -> None:
        """Handle the GET request to this page and render the quote as img."""
        if (file_extension := file_extension.lower()) not in FILE_EXTENSIONS:
            raise HTTPError(
                status_code=400,
                reason=f"Unsupported file extension: {file_extension} "
                f"(supported: {', '.join(FILE_EXTENSIONS.keys())}).",
            )
        file_type = FILE_EXTENSIONS[file_extension]
        wrong_quote = await get_wrong_quote(int(quote_id), int(author_id))

        if not (
            str_to_bool(
                str(self.get_query_argument("no_source", default="False")),
                default=False,
            )
        ):
            _id = (
                wrong_quote.id
                if wrong_quote.id != -1
                else f"{quote_id}-{author_id}"
            )
            source: None | str = f"{self.request.host_name}/z/{_id}"
        else:
            source = None
        self.set_header("Content-Type", f"image/{file_type}")
        if file_type == "gif" and str_to_bool(
            self.get_query_argument("small", default="False"),
            default=False,
        ):
            file_type = "4-color-gif"
        await self.finish(
            create_image(
                wrong_quote.quote.quote,
                wrong_quote.author.name,
                wrong_quote.rating,
                source,
                file_type,
            )
        )
