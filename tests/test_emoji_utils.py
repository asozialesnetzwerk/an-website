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

"""Test utilities for dealing with emojis."""

from an_website.utils.emoji import (
    split_text_into_emoji_and_non_emoji_parts,
    text_contains_emoji,
)


def test_split_text_into_emoji_and_non_emoji_parts() -> None:
    """Test split_text_into_emoji_and_non_emoji_parts."""

    def split(text: str) -> tuple[tuple[str, bool], ...]:
        return tuple(split_text_into_emoji_and_non_emoji_parts(text))

    assert split("abc") == (("abc", False),)
    assert split("abc🤓def") == (("abc", False), ("🤓", True), ("def", False))
    assert split("abc🏃🏽‍♀‍➡") == (("abc", False), ("🏃🏽‍♀‍➡", True))
    assert split("🫃🏼🧑🏻‍🎄👨🏽‍❤️‍👨🏻 ") == (
        ("🫃🏼🧑🏻‍🎄👨🏽‍❤️‍👨🏻", True),
        (" ", False),
    )


def test_text_contains_emoji() -> None:
    """Test text_contains_emoji."""
    assert text_contains_emoji("🫃🏼🧑🏻‍🎄👨🏽‍❤️‍👨🏻 ")
    assert text_contains_emoji("🤓")
    assert text_contains_emoji("🇩🇪")
    assert text_contains_emoji("flag 🇩🇪 test")
    assert not text_contains_emoji("")
    assert not text_contains_emoji("hello, world!")
    assert not text_contains_emoji("\u200B")
    assert not text_contains_emoji("\u200B")
