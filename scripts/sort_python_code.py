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

"""Sort all the python code in this module."""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple, cast

# import black

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_ROOT = Path(REPO_ROOT, "an_website")


def main() -> int | str:
    """Sort the code in the an_website module."""
    errors = []
    file_count = 0
    for file in CODE_ROOT.rglob("*.py"):
        if not file.is_file():
            print(file, "is no file.")
            continue
        file_count += 1
        if err := sort_file(file):
            errors.append((file, err))

    print(f"Sorted {file_count} files and encountered {len(errors)} errors.")

    return "\n".join(f"{file}: {err}" for file, err in errors) if errors else 0


def sort_file(path: Path) -> None | str:
    """Sort a given file."""
    code = path.read_text("utf-8")

    try:
        new_code = sort(code.strip(), path.name)
    except Exception as exc:  # pylint: disable=broad-except
        return f"Sorting failed with {exc}"
    try:
        compile(code, path.name, mode="exec", _feature_version=10)
    except Exception as exc:  # pylint: disable=broad-except
        return f"Sorting destroyed code: {exc}"

    # new_code = black.format_str(
    #     new_code,
    #     mode=black.Mode(
    #         target_versions={
    #             black.TargetVersion.PY310,
    #             black.TargetVersion.PY311,
    #         },
    #         line_length=80,
    #         string_normalization=False,
    #         is_pyi=False,
    #     ),
    # )
    path.write_text(new_code.strip() + "\n", "utf-8")
    return None


class Position(NamedTuple):
    """A position in code."""

    line: int
    col: int


FunctionOrClassDef = (
    ast.FunctionDef
    | ast.ClassDef
    | ast.AsyncFunctionDef
    # | ast.Assign
    # | ast.AnnAssign
)


class BlockOfCode:
    # pylint: disable=too-many-instance-attributes
    """A block of some sort of code."""

    name: None | str
    defines: tuple[str, ...]
    first_line: str
    code: str
    unparsed_code: None | str
    pos: Position
    end_pos: Position
    node: None | FunctionOrClassDef

    def __init__(
        self,
        lines: list[str],
        node: None | FunctionOrClassDef,
        pos: Position,
        end_pos: Position,
    ):
        """Create an instance of this class."""
        self.node = node
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
        if isinstance(node, FunctionOrClassDef):  # type: ignore
            self.name = cast(FunctionOrClassDef, node).name.strip()
            self.defines = (self.name,)
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

    def uses(self, other: BlockOfCode) -> bool:
        """Return if self's code uses stuff from the other block of code."""
        # TODO: improve this
        code = re.sub(r'"""(.|\n)+"""', "", (self.unparsed_code or self.code))
        return any(def_ in code for def_ in other.defines)

    def __lt__(self, other: BlockOfCode) -> bool:
        """Return whether self goes before the other."""
        if not self.name:  # self.uses(other) or
            return False
        if not other.name:  # other.uses(self) or
            return True
        # if (
        #    isinstance(self.node, ast.Assign | ast.AnnAssign)
        #    and not isinstance(other.node, ast.Assign | ast.AnnAssign)
        # ):
        #     return True
        # if (
        #    isinstance(other.node, ast.Assign | ast.AnnAssign)
        #    and not isinstance(self.node, ast.Assign | ast.AnnAssign)
        # ):
        #     return False
        return self.name.lower() < other.name.lower()


def sort(code: str, file_name: str, is_class: bool = False) -> str:
    # pylint: disable=too-complex
    """Sort the classes and functions in a list."""
    if is_class:
        class_ = ast.parse(
            code, file_name, type_comments=True, feature_version=10
        ).body[0]
        assert isinstance(class_, ast.ClassDef)
        nodes = class_.body
    else:
        nodes = ast.parse(
            code, file_name, type_comments=True, feature_version=10
        ).body

    lines = code.split("\n")

    blocks_of_code: list[BlockOfCode] = [
        BlockOfCode(
            lines.copy(),
            node,
            Position(node.lineno - 1, node.col_offset),
            Position(
                cast(int, node.end_lineno) - 1, cast(int, node.end_col_offset)
            ),
        )
        for node in nodes
        # if isinstance(node, FunctionOrClassDef)
        if isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        )  # or not is_class
    ]

    if not blocks_of_code:
        return code

    if is_class:
        for code_block in sorted(
            blocks_of_code, key=lambda func: func.pos.line, reverse=True
        ):
            if len(lines) > code_block.end_pos.line + 1:
                start_line = lines[code_block.end_pos.line + 1]
                # if start_line not in {
                #     'if __name__ == "__main__":',
                #     "if __name__ == '__main__':",
                #     'if "__main__" == __name__:',
                #     "if '__main__' == __name__:",
                # }:
                blocks_of_code.append(
                    BlockOfCode(
                        lines.copy(),
                        None,
                        Position(
                            code_block.end_pos.line + 1,
                            len(start_line) - len(start_line.lstrip()),
                        ),
                        Position(
                            len(lines) - 1, len(lines[len(lines) - 1]) - 1
                        ),
                    )
                )
            lines = lines[: code_block.pos.line]

        blocks_of_code = sorted(blocks_of_code)

    # if not is_class:
    #     for code_block in blocks_of_code.copy():
    #         while any(
    #             dependencies := [
    #                 other
    #                 for other in blocks_of_code[blocks_of_code.index(code_block):]
    #                 if code_block.uses(other) and other is not code_block
    #             ]
    #         ):
    #             for other in dependencies:
    #                 blocks_of_code.remove(other)
    #                 blocks_of_code.insert(blocks_of_code.index(code_block), other)
    #                 if file_name == "utils.py":
    #                     pass
    #     end: list[str] = []
    #     for i, line in enumerate(lines):
    #         if line.strip() in {
    #             'if __name__ == "__main__":',
    #             "if __name__ == '__main__':",
    #             'if "__main__" == __name__:',
    #             "if '__main__' == __name__:",
    #         }:
    #             start = i
    #             while start:
    #                 if lines[start - 1].strip():
    #                     break
    #                 start -= 1
    #             end.extend(lines[start:])
    #             lines = lines[:start]
    #             break

    for code_block in blocks_of_code:
        if isinstance(code_block.node, ast.ClassDef):
            code_block.code = sort(
                code_block.code,
                file_name,
                is_class=True,
            )
            code_lines = code_block.code.split("\n")
            if not is_class:
                for i in range(
                    code_block.pos.line, code_block.end_pos.line + 1
                ):
                    lines[i] = code_lines[i - code_block.pos.line]
        if is_class:
            for line in code_block.code.split("\n"):
                lines.append(line)

    # lines.extend(end)

    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
