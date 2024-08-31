#!/usr/bin/env python3

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

"""Sort all the Python code in this repo."""

from __future__ import annotations

import ast
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cmp_to_key
from os import PathLike
from pathlib import Path
from traceback import format_exception, format_exception_only
from typing import Any, Final, NamedTuple, cast

REPO_ROOT: Final[str] = os.path.dirname(
    os.path.dirname(os.path.normpath(__file__))
)


def main() -> int | str:
    """Sort all the Python code in this repo."""
    errors = []
    changed_count = 0
    file_count = 0
    for path in Path(REPO_ROOT).rglob("*.py"):
        if (
            not path.is_file()
            or path.is_relative_to(os.path.join(REPO_ROOT, ".git"))
            or path.is_relative_to(os.path.join(REPO_ROOT, "venv"))
        ):
            continue
        file_count += 1
        if isinstance(changed := sort_file(path), str):
            errors.append((path.relative_to(REPO_ROOT), changed))
        elif changed:
            changed_count += 1

    print(
        f"Sorted {changed_count}/{file_count} files "
        f"and encountered {len(errors)} errors."
    )

    return "\n".join(f"{file}: {err}" for file, err in errors) if errors else 0


def ast_uses_name(root: ast.AST, name: str) -> bool:
    for node in ast.walk(root):
        if isinstance(node, ast.Name) and node.id == name:
            return True
    return False


def sort_file(file: Path) -> str | bool:
    """Sort a given file."""
    code = file.read_text("UTF-8")

    try:
        new_code = sort_classes(code.strip(), file).strip() + "\n"
    except Exception as exc:  # pylint: disable=broad-except
        error = "".join(format_exception(exc))
        return f"Sorting failed: {error}"

    try:
        compile(new_code, file, "exec")
    except Exception as exc:  # pylint: disable=broad-except
        error = format_exception_only(exc)[-1].strip()
        return f"Sorting destroyed code: {error}"

    if code != new_code:
        file.write_text(new_code, "UTF-8")
        return True

    return False


class Position(NamedTuple):
    """A position in code."""

    line: int
    col: int


@dataclass(frozen=True)
class BlockOfCode:
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """A block of some sort of code."""
    code: str
    defines: tuple[str, ...]
    end_pos: Position
    first_line: str
    is_function: bool

    name: str
    node: ast.AST
    pos: Position
    unparsed_code: None | str

    @staticmethod
    def compare(a: BlockOfCode, b: BlockOfCode) -> int:
        """Compare two blocks of code."""
        if a.uses(b):
            return 1
        if b.uses(a):
            return -1
        if a.is_function and not b.is_function:
            return 1
        if not a.is_function and b.is_function:
            return -1
        if a.name < b.name:
            return -1
        if a.name > b.name:
            return 1
        return 0

    @staticmethod
    def create(
        lines: Sequence[str],
        node: ast.AST,
        pos: Position,
        end_pos: Position,
    ) -> BlockOfCode | None:
        """Create an instance of this class."""
        match node:
            case ast.AST(name=str(name)):  # type: ignore[misc]
                defines = (name,)
            case ast.AnnAssign(target=ast.Name(id=str(name))):
                defines = (name,)
            case ast.Assign(targets=[ast.Name(id=str(name))]):
                defines = (name,)
            case _:
                return None

        if name:
            assert name.strip() == name

        line_idx = pos.line
        indentation = " " * pos.col

        try:
            assert lines[pos.line].startswith(indentation)
        except AssertionError:
            print(node, pos)
            return None

        while line_idx:  # pylint: disable=while-used
            if (
                not lines[line_idx - 1].startswith(f"{indentation}@")
                and not lines[line_idx - 1].startswith(f"{indentation}#")
                and lines[line_idx - 1].strip()
            ):
                break
            line_idx -= 1
            pos = Position(line_idx, pos.col)

        return BlockOfCode(
            is_function=isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ),
            node=node,
            code="\n".join(lines[pos.line : end_pos.line + 1]),  # noqa: E203
            first_line=lines[pos.line],
            name=name,
            defines=defines,
            unparsed_code=ast.unparse(node),
            pos=pos,
            end_pos=end_pos,
        )

    def uses(self, other: BlockOfCode) -> bool:
        """Return if self's code uses stuff from the other block of code."""
        return ast_uses_name(self.node, other.name)


def sort_class(
    code: str, filename: str | bytes | PathLike[Any] = "<unknown>"
) -> list[str]:
    """Sort the methods of a class and return the code as lines."""
    module = compile(code, filename, "exec", ast.PyCF_ONLY_AST)
    assert isinstance(module, ast.Module)
    class_ = module.body[0]
    assert isinstance(class_, ast.ClassDef)

    lines = code.split("\n")

    functions = list(  # get all the functions in the class
        filter(
            None,
            (
                BlockOfCode.create(
                    lines.copy(),
                    node,
                    Position(node.lineno - 1, node.col_offset),
                    Position(
                        cast(int, node.end_lineno) - 1,
                        cast(int, node.end_col_offset),
                    ),
                )
                for node in class_.body
            ),
        ),
    )

    for function in sorted(
        functions, key=lambda func: func.pos.line, reverse=True
    ):  # remove functions from lines
        lines = (
            lines[: function.pos.line]
            + lines[1 + function.end_pos.line :]  # noqa: E203
        )

    for function in sorted(functions, key=cmp_to_key(BlockOfCode.compare)):
        lines.extend(function.code.split("\n"))

    return lines


def sort_classes(
    code: str, filename: str | bytes | PathLike[Any] = "<unknown>"
) -> str:
    """Sort the classes and functions in a module."""
    module = compile(code, filename, "exec", ast.PyCF_ONLY_AST)
    assert isinstance(module, ast.Module)
    nodes = module.body

    lines = code.split("\n")

    classes: list[BlockOfCode] = list(
        filter(
            None,
            (
                BlockOfCode.create(
                    lines.copy(),
                    node,
                    Position(node.lineno - 1, node.col_offset),
                    Position(
                        cast(int, node.end_lineno) - 1,
                        cast(int, node.end_col_offset),
                    ),
                )
                for node in nodes
                if isinstance(node, ast.ClassDef)
            ),
        )
    )

    if not classes:
        return code

    if isinstance(filename, PathLike):
        filename = cast(str | bytes, os.fspath(filename))

    if isinstance(filename, str):
        filename = filename.encode("UTF-8")

    for class_ in classes:
        class_lines = sort_class(
            class_.code,
            b"%b|%b" % (filename, str(class_.name).encode("UTF-8")),
        )
        assert len(class_.code.split("\n")) == len(class_lines)
        for i, line in enumerate(class_lines):
            lines[i + class_.pos.line] = line

    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
