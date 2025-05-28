"""Module for manipulating code: linting, formatting, and import restructuring."""


# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import warnings
from collections import deque
from typing import TYPE_CHECKING, Any

import isort
import libcst as cst
import rich

from . import constants, unix
from . import file_utilities as futils

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterable, Mapping


class LinterWarning(RuntimeWarning):
    """Found linting issues."""


class TypeCheckerWarning(RuntimeWarning):
    """Found type check issues."""


def lint_python_files(paths: Iterable[pathlib.Path]) -> None:
    """Run a linter on python files."""
    paths = [p for p in paths if p.is_dir() or futils.is_python_file(p)]
    ruff_status, ruff_message = unix.ruff_check(paths, fix=True)
    rich.print(ruff_message)
    if ruff_status != 0:
        warnings.warn("Found linting issues", LinterWarning, stacklevel=1)


def lint_and_fix_python_files(paths: Iterable[pathlib.Path]) -> None:
    """Run a linter on python files and fix the fixable issues."""
    paths = [p for p in paths if p.is_dir() or futils.is_python_file(p)]
    ruff_status, ruff_message = unix.ruff_check(paths, fix=False)
    rich.print(ruff_message)
    if ruff_status != 0:
        warnings.warn("Found linting issues", LinterWarning, stacklevel=1)


def static_type_check_python_files(paths: Iterable[pathlib.Path]) -> None:
    """Run a type checker on python files."""
    paths = [p for p in paths if p.is_dir() or futils.is_python_file(p)]
    mypy_status, mypy_message = unix.mypy(paths)
    rich.print(mypy_message)
    if mypy_status != 0:
        warnings.warn("Found type check issues", TypeCheckerWarning, stacklevel=1)


def format_python_files(paths: Iterable[pathlib.Path]) -> None:
    """Format python files."""
    paths = [p for p in paths if p.is_dir() or futils.is_python_file(p)]
    sort_imports(paths)
    _, results = unix.ruff_format(paths)
    rich.print(results)


def format_json_files(paths: Iterable[pathlib.Path]) -> None:
    """Format json files."""
    paths = [p for p in paths if futils.is_json_file(p)]
    for path in paths:
        if path.is_file():
            futils.replace_file_content(path, replace_fn=format_json)

        elif path.is_dir():
            for file in path.rglob("*.*def"):
                if futils.is_json_file(file):
                    futils.replace_file_content(file, replace_fn=format_json)


def format_json(str_content: str) -> str:
    """Format JSON content.

    Args:
        str_content: the JSON string to format

    Returns:
        The formatted JSON string.

    """
    json_content: Mapping[str, Any] = json.loads(str_content)
    return json.dumps(json_content, indent=4, sort_keys=True)


def sort_imports(paths: Iterable[pathlib.Path]) -> None:
    """Sort imports in python files."""
    paths = [p for p in paths if p.suffix == ".py"]
    for path in paths:
        if path.is_file():
            futils.replace_file_content(path, replace_fn=isort.code)

        elif path.is_dir():
            for file in path.rglob("*.py"):
                futils.replace_file_content(file, replace_fn=isort.code)


def restructure_scripts_imports(paths: Iterable[pathlib.Path]) -> None:
    """Restructure script imports in python files.

    Args:
        paths: the paths of the files to be modified.

    """
    paths = [p for p in paths if p.suffix == ".py"]
    for path in paths:
        futils.replace_file_content(path, replace_fn=restructure_script_imports)


def restructure_script_imports(code_string: str) -> str:
    """Restructure script imports in python files.

    Args:
        code_string: the code string to be modified.

    Returns:
        The modified code string.

    """
    tree: cst.Module = cst.parse_module(code_string)
    transformer: ImportTransformer = ImportTransformer()
    modified_tree: cst.Module = tree.visit(transformer)
    return modified_tree.code


class ImportTransformer(cst.CSTTransformer):
    def leave_ImportFrom(  # noqa: D102, N802
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.ImportFrom | cst.Import:
        # `from ...common.module... import ...` => `from module import module...`
        # `from ...core.module... import ...` => `from module import module...`
        # `from ...soar_sdk.module... import ...` => `from module import module...`
        nodes: deque[cst.Attribute] = _get_attribute_list(original_node)
        if nodes and _is_reserved_node(nodes[0]):
            node: cst.Attribute | cst.Name = _rebuild_attributes(nodes)
            return updated_node.with_changes(relative=[], module=node)

        match original_node:
            # `from .(nothing or reserved) import ...` => `import ...`
            case cst.ImportFrom(
                module=(
                    None
                    | cst.Name(
                        value=(
                            constants.CORE_SCRIPTS_DIR
                            | constants.COMMON_SCRIPTS_DIR
                            | constants.SDK_PACKAGE_NAME
                        ),
                    )
                ),
                names=names,
            ):
                return cst.Import(names=names)  # type: ignore[arg-type]

            # `from .module import ...` => `from module import ...`
            case cst.ImportFrom(relative=[cst.Dot(), *_]):
                return updated_node.with_changes(relative=[])

            case _:
                return updated_node


def _is_reserved_node(node: cst.Attribute) -> bool:
    return isinstance(name := node.value, cst.Name) and name.value in {
        constants.COMMON_SCRIPTS_DIR,
        constants.CORE_SCRIPTS_DIR,
        constants.SDK_PACKAGE_NAME,
    }


def _get_attribute_list(node: cst.ImportFrom) -> deque[cst.Attribute]:
    nodes: deque[cst.Attribute] = deque()
    current_node: cst.Name | cst.Attribute | None = node.module
    while isinstance(current_node, cst.Attribute):
        nodes.appendleft(current_node)
        current_node = current_node.value  # type: ignore[assignment]

    return nodes


def _rebuild_attributes(nodes: deque[cst.Attribute]) -> cst.Attribute | cst.Name:
    attribute: cst.Attribute = nodes.popleft()
    current: cst.Attribute | cst.Name = attribute.attr
    for node in nodes:
        current = node.with_changes(value=current)

    return current
