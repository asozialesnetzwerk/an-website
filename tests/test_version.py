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

"""The tests for the version module."""

from an_website.version.version import (
    get_file_hashes,
    get_hash_of_file_hashes,
    hash_all_files,
    hash_bytes,
)


def test_hash_bytes() -> None:
    """Test the hash_bytes function."""
    assert hash_bytes(b"") == "⢜⠑⢅⢥⣅⣩⣼⡔⡡⠨⠈⢗⡾⣨⣵⡈⢲⠥⢍⠱"
    assert hash_bytes(b"26.5") == "⣛⢈⢁⢵⡀⢛⠡⣧⡠⡽⠥⢘⣋⡁⠬⣦⡙⠺⠸⠢"
    assert hash_bytes(b"1.1.1.1") == "⠍⢹⠪⣴⠊⣢⠲⡹⠿⢚⣡⡑⡙⠤⣅⠜⣼⡪⢧⠐"
    assert hash_bytes(b"an-website") == "⢙⠐⣥⡩⣯⡶⣥⣂⡱⢁⣐⢆⡐⢻⢢⢳⣈⡻⢫⡿"
    assert hash_bytes(bytes(range(67))) == "⡝⣥⠋⢻⠑⣆⠪⢾⠢⣧⣭⣂⢈⢷⣑⢶⢡⣏⣌⡠"
    assert hash_bytes(bytes(range(256))) == "⢜⡏⢠⡲⣛⠬⢇⠚⡖⠵⣣⡿⡹⠞⢓⢫⡅⠄⢖⡶"


def test_get_file_hashes() -> None:
    """Test the get_file_hashes function."""
    assert isinstance(get_file_hashes(), str)
    assert "version.py" in get_file_hashes()
    assert get_file_hashes() == get_file_hashes()
    assert get_file_hashes() == hash_all_files()


def test_hash_all_files() -> None:
    """Test the hash_all_files function."""
    assert isinstance(hash_all_files(), str)
    assert "version.py" in hash_all_files()
    assert hash_all_files() == hash_all_files()
    assert hash_all_files() == get_file_hashes()


def test_get_hash_of_file_hashes() -> None:
    """Test the get_hash_of_file_hashes function."""
    assert isinstance(get_hash_of_file_hashes(), str)
    assert len(get_hash_of_file_hashes()) == 20
    assert get_hash_of_file_hashes() == get_hash_of_file_hashes()
    chars = (ord(ch) for ch in get_hash_of_file_hashes())
    assert all(ch in range(0x2800, 0x2900) for ch in chars)
