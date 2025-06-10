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

"""A module that generates an image from a wrong quote."""

from __future__ import annotations

import asyncio
import io
import logging
import math
import os
import sys
import textwrap
import time
from collections import ChainMap
from collections.abc import Iterable, Mapping, Set
from tempfile import TemporaryDirectory
from typing import Any, ClassVar, Final

import qoi_rs
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import new as create_empty_image
from tornado.web import HTTPError

from .. import EPOCH
from ..utils import static_file_handling
from .utils import (
    DIR,
    QuoteReadyCheckHandler,
    get_wrong_quote,
    get_wrong_quotes,
)

try:
    from unexpected_isaves.save_image import (  # type: ignore[import, unused-ignore]
        to_excel,
    )
except ModuleNotFoundError:
    to_excel = None  # pylint: disable=invalid-name

LOGGER: Final = logging.getLogger(__name__)

AUTHOR_MAX_WIDTH: Final[int] = 686
QUOTE_MAX_WIDTH: Final[int] = 900
DEBUG_COLOR: Final[tuple[int, int, int]] = 245, 53, 170
DEBUG_COLOR2: Final[tuple[int, int, int]] = 224, 231, 34
TEXT_COLOR: Final[tuple[int, int, int]] = 230, 230, 230

with (DIR / "files/oswald.regular.ttf").open("rb") as data:
    FONT: Final = ImageFont.truetype(font=data, size=50)
with (DIR / "files/oswald.regular.ttf").open("rb") as data:
    FONT_SMALLER: Final = ImageFont.truetype(font=data, size=44)
with (DIR / "files/oswald.regular.ttf").open("rb") as data:
    HOST_NAME_FONT: Final = ImageFont.truetype(font=data, size=23)
del data

FILE_EXTENSIONS: Final[Mapping[str, str]] = {
    "bmp": "bmp",
    "gif": "gif",
    "jfif": "jpeg",
    "jpe": "jpeg",
    "jpeg": "jpeg",
    "jpg": "jpeg",
    "jxl": "jxl",
    "pdf": "pdf",
    "png": "png",
    # "ppm": "ppm",
    # "sgi": "sgi",
    "spi": "spider",
    "spider": "spider",
    "tga": "tga",
    "tiff": "tiff",
    "txt": "txt",
    "webp": "webp",
    "qoi": "qoi",
    **({"xlsx": "xlsx"} if to_excel else {}),
}

CONTENT_TYPES: Final[Mapping[str, str]] = ChainMap(
    {
        "spider": "image/x-spider",
        "tga": "image/x-tga",
        "qoi": "image/qoi",
    },
    static_file_handling.CONTENT_TYPES,  # type: ignore[arg-type]
)

CONTENT_TYPE_FILE_TYPE_MAPPING: Final[Mapping[str, str]] = {
    CONTENT_TYPES[ext]: ext for ext in FILE_EXTENSIONS.values()
}
IMAGE_CONTENT_TYPES: Final[Set[str]] = frozenset(CONTENT_TYPE_FILE_TYPE_MAPPING)
IMAGE_CONTENT_TYPES_WITHOUT_TXT: Final[tuple[str, ...]] = tuple(
    sorted(IMAGE_CONTENT_TYPES - {"text/plain"}, key="image/gif".__ne__)
)


def load_png(filename: str) -> Image.Image:
    """Load a PNG image into memory."""
    with (DIR / "files" / f"{filename}.png").open("rb") as file:  # noqa: SIM117
        with Image.open(file, formats=("PNG",)) as image:
            return image.copy()


BACKGROUND_IMAGE: Final = load_png("bg")
IMAGE_WIDTH, IMAGE_HEIGHT = BACKGROUND_IMAGE.size
WITZIG_IMAGE: Final = load_png("StempelWitzig")
NICHT_WITZIG_IMAGE: Final = load_png("StempelNichtWitzig")


def get_lines_and_max_height(
    text: str,
    max_width: int,
    font: ImageFont.FreeTypeFont,
) -> tuple[list[str], int]:
    """Get the lines of the text and the max line height."""
    column_count = 46
    lines: list[str] = []

    max_line_length: float = max_width + 1
    while max_line_length > max_width:  # pylint: disable=while-used
        lines = textwrap.wrap(text, width=column_count)
        max_line_length = max(font.getlength(line) for line in lines)
        column_count -= 1

    return lines, max(font.getbbox(line)[3] for line in lines)


def draw_text(  # pylint: disable=too-many-arguments
    image: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    stroke_width: int = 0,
    *,
    display_bounds: bool = sys.flags.dev_mode,
) -> None:
    """Draw a text on an image."""
    image.text(
        (x, y),
        text,
        font=font,
        fill=TEXT_COLOR,
        align="right",
        stroke_width=stroke_width,
        spacing=54,
    )
    if display_bounds:
        x_off, y_off, right, bottom = font.getbbox(
            text, stroke_width=stroke_width
        )
        image.rectangle((x, y, x + right, y + bottom), outline=DEBUG_COLOR)
        image.rectangle(
            (x + x_off, y + y_off, x + right, y + bottom), outline=DEBUG_COLOR2
        )


def draw_lines(  # pylint: disable=too-many-arguments
    image: ImageDraw.ImageDraw,
    lines: Iterable[str],
    y_start: int,
    max_w: int,
    max_h: int,
    font: ImageFont.FreeTypeFont,
    padding_left: int = 0,
    stroke_width: int = 0,
) -> int:
    """Draw the lines on the image and return the last y position."""
    for line in lines:
        width = font.getlength(line)
        draw_text(
            image,
            line,
            padding_left + math.ceil((max_w - width) / 2),
            y_start,
            font,
            stroke_width,
        )
        y_start += max_h
    return y_start


def create_image(  # noqa: C901  # pylint: disable=too-complex
    # pylint: disable=too-many-arguments, too-many-branches
    # pylint: disable=too-many-locals, too-many-statements
    quote: str,
    author: str,
    rating: None | int,
    source: None | str,
    file_type: str = "png",
    font: ImageFont.FreeTypeFont = FONT,
    *,
    include_kangaroo: bool = True,
    wq_id: None | str = None,
) -> bytes:
    """Create an image with the given quote and author."""
    image = (
        BACKGROUND_IMAGE.copy()
        if include_kangaroo
        else create_empty_image("RGB", BACKGROUND_IMAGE.size, 0)
    )
    draw = ImageDraw.Draw(image, mode="RGB")

    # draw quote
    quote_str = f"»{quote}«"
    width, max_line_height = font.getbbox(quote_str)[2:]
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
        0,
        1 if file_type == "4-color-gif" else 0,
    )

    # draw author
    author_str = f"- {author}"
    width, max_line_height = font.getbbox(author_str)[2:]
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
        1 if file_type == "4-color-gif" else 0,
    )

    if y_text > IMAGE_HEIGHT and font is FONT:
        LOGGER.info("Using smaller font for quote %s", source)
        return create_image(
            quote,
            author,
            rating,
            source,
            file_type,
            FONT_SMALLER,
            wq_id=wq_id,
        )

    # draw rating
    if rating:
        _, y_off, width, height = FONT_SMALLER.getbbox(str(rating))
        y_rating = IMAGE_HEIGHT - 25 - height
        draw_text(
            draw,
            str(rating),
            25,
            y_rating,
            FONT_SMALLER,  # always use same font for rating
            1,
        )
        # draw rating image
        icon = NICHT_WITZIG_IMAGE if rating < 0 else WITZIG_IMAGE
        image.paste(
            icon,
            box=(
                25 + 5 + width,
                y_rating + y_off // 2,
            ),
            mask=icon,
        )

    # draw host name
    if source:
        width, height = HOST_NAME_FONT.getbbox(source)[2:]
        draw_text(
            draw,
            source,
            IMAGE_WIDTH - 5 - width,
            IMAGE_HEIGHT - 5 - height,
            HOST_NAME_FONT,
            0,
        )

    if file_type == "qoi":
        return qoi_rs.encode_pillow(image)

    if to_excel and file_type == "xlsx":
        with TemporaryDirectory() as tempdir_name:
            filepath = os.path.join(tempdir_name, f"{wq_id or '0-0'}.xlsx")
            to_excel(image, filepath, lower_image_size_by=10)
            with open(filepath, "rb") as file:
                return file.read()

    kwargs: dict[str, Any] = {
        "format": file_type,
        "optimize": True,
        "save_all": False,
    }

    if file_type == "4-color-gif":
        colors: list[tuple[int, tuple[int, int, int]]]
        colors = image.getcolors(2**16)  # type: ignore[assignment]
        colors.sort(reverse=True)
        palette = bytearray()
        for _, color in colors[:4]:
            palette.extend(color)
        kwargs.update(format="gif", palette=palette)
    elif file_type == "jxl":
        kwargs.update(lossless=True)
    elif file_type == "pdf":
        timestamp = time.gmtime(EPOCH)
        kwargs.update(
            title=wq_id or "0-0",
            author=author,
            subject=quote,
            creationDate=timestamp,
            modDate=timestamp,
        )
    elif file_type == "tga":
        kwargs.update(compression="tga_rle")
    elif file_type == "tiff":
        kwargs.update(compression="zlib")
    elif file_type == "webp":
        kwargs.update(lossless=True)

    image.save(buffer := io.BytesIO(), **kwargs)
    return buffer.getvalue()


class QuoteAsImage(QuoteReadyCheckHandler):
    """Quote as image request handler."""

    POSSIBLE_CONTENT_TYPES: ClassVar[tuple[str, ...]] = ()
    RATELIMIT_GET_LIMIT: ClassVar[int] = 15

    async def get(
        self,
        quote_id: str,
        author_id: str,
        file_extension: None | str = None,
        *,
        head: bool = False,
    ) -> None:
        """Handle GET requests to this page and render the quote as image."""
        file_type: None | str
        if file_extension is None:
            self.handle_accept_header(IMAGE_CONTENT_TYPES_WITHOUT_TXT)
            assert self.content_type
            file_type = CONTENT_TYPE_FILE_TYPE_MAPPING[self.content_type]
            file_extension = file_type
        elif not (file_type := FILE_EXTENSIONS.get(file_extension.lower())):
            reason = (
                f"Unsupported file extension: {file_extension.lower()} (supported:"
                f" {', '.join(sorted(set(FILE_EXTENSIONS.values())))})"
            )
            self.set_status(404, reason=reason)
            self.write_error(404, reason=reason)
            return

        content_type = CONTENT_TYPES[file_type]

        self.handle_accept_header((content_type,))

        int_quote_id = int(quote_id)
        wrong_quote = (
            await get_wrong_quote(int_quote_id, int(author_id))
            if author_id
            else (
                get_wrong_quotes(lambda wq: wq.id == int_quote_id) or (None,)
            )[0]
        )
        if wrong_quote is None:
            raise HTTPError(404, reason="Falsches Zitat nicht gefunden")

        if file_type == "txt":
            await self.finish(str(wrong_quote))
            return

        self.set_header(
            "Content-Disposition",
            (
                f"inline; filename={self.request.host.replace('.', '-')}_z_"
                f"{wrong_quote.get_id_as_str()}.{file_extension.lower()}"
            ),
        )

        if head:
            return

        if file_type == "gif" and self.get_bool_argument("small", False):
            file_type = "4-color-gif"

        return await self.finish(
            await asyncio.to_thread(
                create_image,
                wrong_quote.quote.quote,
                wrong_quote.author.name,
                rating=(
                    None
                    if self.get_bool_argument("no_rating", False)
                    else wrong_quote.rating
                ),
                source=(
                    None
                    if self.get_bool_argument("no_source", False)
                    else f"{self.request.host_name}/z/{wrong_quote.get_id_as_str(True)}"
                ),
                file_type=file_type,
                include_kangaroo=not self.get_bool_argument(
                    "no_kangaroo", False
                ),
                wq_id=wrong_quote.get_id_as_str(),
            )
        )
