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

"""Utilities for dealing with emojis."""

from collections.abc import Iterable
from typing import TypeGuard

from emoji import EmojiMatch, Token, analyze
from emoji.tokenizer import tokenize


def _is_emoji_token(token: Token) -> TypeGuard[Token]:
    """Check if the token represents an emoji."""
    return isinstance(token.value, EmojiMatch)


def split_text_into_emoji_and_non_emoji_parts(
    text: str,
) -> Iterable[tuple[str, bool]]:
    """Return tuple of strings and is_emoji bools."""
    it = iter(analyze(text, non_emoji=True, join_emoji=True))

    try:
        first = next(it)
    except StopIteration:
        return

    chars = [first.chars]
    is_emoji = _is_emoji_token(first)

    for value in it:
        if is_emoji != _is_emoji_token(value):
            yield ("".join(chars), is_emoji)
            chars.clear()
            is_emoji = not is_emoji

        chars.append(value.chars)

    if chars:
        yield ("".join(chars), is_emoji)


def text_contains_emoji(text: str) -> bool:
    """Check if the given string contains at-least one emoji."""
    # pylint: disable-next=bad-builtin
    return any(filter(_is_emoji_token, tokenize(text, False)))
