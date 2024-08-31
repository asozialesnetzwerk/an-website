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
import re  # pylint: disable=preferred-module
import sys
from collections.abc import Sequence
from functools import cmp_to_key
from os import PathLike
from pathlib import Path
from traceback import format_exception_only
from typing import Any, Final, NamedTuple, TypeAlias, cast
from urllib.parse import uses_query

REPO_ROOT: Final[str] = os.path.dirname(
    os.path.dirname(os.path.normpath(__file__))
)

FunctionOrClassDef: TypeAlias = (
    # ast.AnnAssign
    # | ast.Assign
    ast.AsyncFunctionDef
    | ast.ClassDef
    | ast.FunctionDef
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
    """Return true if the AST uses the given name."""
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
        error = format_exception_only(exc)[-1].strip()
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


class BlockOfCode:
    # pylint: disable=too-many-instance-attributes, too-few-public-methods
    """A block of some sort of code."""

    name: None | str
    defines: tuple[str, ...]
    first_line: str
    code: str
    unparsed_code: None | str
    pos: Position
    end_pos: Position
    node: None | FunctionOrClassDef
    uses: tuple[str, ...]

    def __init__(
        self,
        lines: Sequence[str],
        node: None | FunctionOrClassDef,
        pos: Position,
        end_pos: Position,
        uses: tuple[str, ...] = (),
    ):
        """Create an instance of this class."""
        self.node = node
        self.uses = uses
        # if isinstance(node, ast.Assign):
        #     text = lines[
        #         node.targets[0].lineno - 1 : node.targets[-1].end_lineno
        #     ]
        #     text[-1] = text[-1][: node.targets[-1].end_col_offset]
        #     self.name = "\n".join(text).strip()
        #     if len(node.targets) > 1:
        #         self.defines = tuple(
        #             target.strip() for target in self.name.split(",")
        #         )
        #     else:
        #         self.defines = (self.name,)
        # elif isinstance(node, ast.AnnAssign):
        #     self.name = lines[node.target.lineno - 1][
        #         : node.target.end_col_offset
        #     ].strip()
        #     self.defines = (self.name,)
        # el
        if hasattr(node, "name"):
            self.name = cast(Any, node).name.strip()
            self.defines = (self.name,)  # type: ignore[assignment]
        else:
            self.name = None
            self.defines = ()
        self.unparsed_code = ast.unparse(node) if node else None
        self.pos = pos
        self.end_pos = end_pos
        self.first_line = lines[self.pos.line]
        line_idx = self.pos.line
        indentation = " " * self.pos.col
        assert self.first_line.startswith(indentation)

        while line_idx:  # pylint: disable=while-used
            if (
                not lines[line_idx - 1].startswith(f"{indentation}@")
                and not lines[line_idx - 1].startswith(f"{indentation}#")
                and lines[line_idx - 1].strip()
            ):
                break
            line_idx -= 1
            self.pos = Position(line_idx, self.pos.col)

        self.code = "\n".join(
            lines[self.pos.line : self.end_pos.line + 1]  # noqa: E203
        )


def sort_class(
    code: str, filename: str | bytes | PathLike[Any] = "<unknown>"
) -> list[str]:
    """Sort the methods of a class and return the code as lines."""
    module = compile(code, filename, "exec", ast.PyCF_ONLY_AST)
    assert isinstance(module, ast.Module)
    class_ = module.body[0]
    assert isinstance(class_, ast.ClassDef)

    lines = code.split("\n")

    functions: list[BlockOfCode] = []

    for node in class_.body:
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            functions.append(
                BlockOfCode(
                    lines.copy(),
                    node,
                    Position(node.lineno - 1, node.col_offset),
                    Position(
                        cast(int, node.end_lineno) - 1,
                        cast(int, node.end_col_offset),
                    ),
                )
            )
            continue
        uses: list[str] = []
        for fun in functions:
            uses.extend(
                name for name in fun.defines if ast_uses_name(node, name)
            )
        if not uses:
            continue
        functions.append(
            BlockOfCode(
                lines.copy(),
                node,
                Position(node.lineno - 1, node.col_offset),
                Position(
                    cast(int, node.end_lineno) - 1,
                    cast(int, node.end_col_offset),
                ),
                uses=tuple(uses),
            ),
        )

    for function in sorted(
        functions, key=lambda func: func.pos.line, reverse=True
    ):  # remove functions from lines
        lines = (
            lines[: function.pos.line]
            + lines[1 + function.end_pos.line :]  # noqa: E203
        )

    def compare(a: BlockOfCode, b: BlockOfCode) -> int:
        """Compare two blocks."""
        if set(a.uses) & set(b.defines):
            return 1
        if set(b.uses) & set(a.defines):
            return -1
        if (a.name or "").lower() > (b.name or "").lower():
            return 1
        if (a.name or "").lower() < (b.name or "").lower():
            return -1
        return 0

    for function in sorted(functions, key=cmp_to_key(compare)):
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

    classes: list[BlockOfCode] = [
        BlockOfCode(
            lines.copy(),
            node,
            Position(node.lineno - 1, node.col_offset),
            Position(
                cast(int, node.end_lineno) - 1, cast(int, node.end_col_offset)
            ),
        )
        for node in nodes
        if isinstance(node, ast.ClassDef)
    ]

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
