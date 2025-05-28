"""Module containing utility functions for interacting with the file system.

Used for things such as path manipulation and file content operations.
"""

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

import pathlib
import re
import shutil
from typing import TYPE_CHECKING, Any

import yaml

from . import config, constants
from .custom_types import ManagerName, Products

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Callable, Mapping, Sequence


VALID_REPEATED_FILES: set[str] = {"__init__.py"}


def get_community_path() -> pathlib.Path:
    """Get the community integrations' path.

    Returns:
        The community integrations' directory path

    """
    return get_integrations_path() / constants.COMMUNITY_DIR_NAME


def get_commercial_path() -> pathlib.Path:
    """Get the commercial integrations' path.

    Returns:
        The commercial integrations' directory path

    """
    return get_integrations_path() / constants.COMMERCIAL_DIR_NAME


def get_integrations_path() -> pathlib.Path:
    """Get the integrations' path.

    Returns:
        The integrations' directory path

    """
    return config.get_marketplace_path() / constants.INTEGRATIONS_DIR_NAME


def discover_core_modules(path: pathlib.Path) -> list[ManagerName]:
    """Discover core/manager modules in an integration.

    Args:
        path: The path to the integration

    Returns:
        A list of all manager file names

    """
    if is_built(path) or is_half_built(path):
        return sorted(
            [
                p.stem
                for p in (path / constants.OUT_MANAGERS_SCRIPTS_DIR).rglob("*.py")
                if p.is_file() and p.stem not in {"__init__", "__main__"}
            ],
        )

    return sorted(
        [
            p.stem
            for p in (path / constants.CORE_SCRIPTS_DIR).rglob("*.py")
            if p.is_file() and p.stem not in {"__init__", "__main__"}
        ],
    )


def get_integrations_and_groups_from_paths(
    *paths: pathlib.Path,
) -> Products[set[pathlib.Path]]:
    """Get all integrations and integration groups paths from the provided paths.

    Args:
        *paths: The paths to search integrations and groups in

    Returns:
        A `Products` object that contains sets of all the integrations and groups paths
        that were found

    """
    integrations: set[pathlib.Path] = set()
    groups: set[pathlib.Path] = set()
    for path in paths:
        for dir_ in path.iterdir():
            if is_group(dir_):
                groups.add(dir_)

            elif is_integration(dir_):
                integrations.add(dir_)

    return Products(integrations=integrations, groups=groups)


def is_python_file(path: pathlib.Path) -> bool:
    """Check whether a path is a python file.

    Returns:
        Whether the provided file is of a python file

    """
    return path.exists() and path.is_file() and path.suffix == ".py"


def is_json_file(path: pathlib.Path) -> bool:
    """Check whether a path is a JSON file.

    Returns:
        Whether the provided file is of a JSON file

    """
    return path.is_file() and re.fullmatch(r"\.json|\..*def", path.suffix) is not None


def is_integration(path: pathlib.Path, *, group: str = "") -> bool:
    """Check whether a path is an integration.

    Returns:
        Whether the provided path is an integration

    """
    parents: set[str] = {p.name for p in (path, *path.parents)}
    valid_base_dirs: set[str] = {
        constants.COMMUNITY_DIR_NAME,
        constants.COMMERCIAL_DIR_NAME,
    }

    if group:
        valid_base_dirs.add(group)

    return bool(parents.intersection(valid_base_dirs) and _is_integration(path))


def _is_integration(path: pathlib.Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    pyproject_toml: pathlib.Path = path / constants.PROJECT_FILE
    def_: pathlib.Path = path / constants.INTEGRATION_DEF_FILE.format(path.name)
    return pyproject_toml.exists() or def_.exists()


def is_group(path: pathlib.Path) -> bool:
    """Check whether a path is an integration group.

    Returns:
        Whether the provided path is an integration group

    """
    parents: set[str] = {p.name for p in (path, *path.parents)}
    valid_base_dirs: tuple[str, ...] = (
        constants.COMMUNITY_DIR_NAME,
        constants.COMMERCIAL_DIR_NAME,
    )
    return bool(parents.intersection(valid_base_dirs) and _is_group(path))


def _is_group(path: pathlib.Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    return not is_integration(path) and all(
        is_integration(p, group=path.name) for p in path.iterdir() if p.is_dir()
    )


def replace_file_content(file: pathlib.Path, replace_fn: Callable[[str], str]) -> None:
    """Replace a file's entire content.

    Args:
        file: The file to replace its content
        replace_fn: A function that takes in the current file's content and returns
            the new content that will be written into the file

    """
    file_content: str = file.read_text(encoding="utf-8")
    file_content = replace_fn(file_content)
    file.write_text(file_content, encoding="utf-8")


def remove_paths_if_exists(*paths: pathlib.Path) -> None:
    """Remove all the provided paths."""
    for path in paths:
        _remove_path_if_exists(path)


def _remove_path_if_exists(path: pathlib.Path) -> None:
    if path.is_file() and is_path_in_marketplace(path):
        path.unlink(missing_ok=True)

    elif path.is_dir() and path.exists() and is_path_in_marketplace(path):
        shutil.rmtree(path)


def remove_and_create_dir(path: pathlib.Path) -> None:
    """Remove the provided directory and create a new one."""
    if path.exists() and is_path_in_marketplace(path):
        shutil.rmtree(path)
        path.mkdir()


def is_path_in_marketplace(path: pathlib.Path) -> bool:
    """Check whether a path is in the marketplace.

    This is mostly used to ensure any file deletion will not occur outside the
    boundaries of the configured project.

    Returns:
        Whether the path is a sub path of the configured marketplace.

    """
    return config.get_marketplace_path() in path.parents


def is_built(integration: pathlib.Path) -> bool:
    """Check whether an integration is built.

    Returns:
        Whether the integration is in a built format

    """
    pyproject: pathlib.Path = integration / constants.PROJECT_FILE
    def_file: pathlib.Path = integration / constants.INTEGRATION_DEF_FILE.format(
        integration.name,
    )
    definition_file: pathlib.Path = integration / constants.DEFINITION_FILE
    return not pyproject.exists() and def_file.exists() and not definition_file.exists()


def is_half_built(integration: pathlib.Path) -> bool:
    """Check whether an integration is half-built.

    Returns:
        Whether the integration is in a half-built format

    """
    pyproject: pathlib.Path = integration / constants.PROJECT_FILE
    def_file: pathlib.Path = integration / constants.INTEGRATION_DEF_FILE.format(
        integration.name,
    )
    return pyproject.exists() and def_file.exists()


def is_non_built(integration: pathlib.Path) -> bool:
    """Check whether an integration is non-built.

    Returns:
        Whether the integration is in a non-built format

    """
    pyproject: pathlib.Path = integration / constants.PROJECT_FILE
    def_file: pathlib.Path = integration / constants.INTEGRATION_DEF_FILE.format(
        integration.name,
    )
    definition_file: pathlib.Path = integration / constants.DEFINITION_FILE
    return pyproject.exists() and definition_file.exists() and not def_file.exists()


def flatten_dir(path: pathlib.Path, dest: pathlib.Path) -> None:
    """Flatten a nested directory.

    Args:
        path: The path to the directory to flatten
        dest: The destination of the flattened dir

    Raises:
        FileExistsError: If more than one file with the same name is found

    """
    if path.is_file() and is_path_in_marketplace(path):
        new_path: pathlib.Path = dest / path.name
        if new_path.exists():
            if new_path.name in VALID_REPEATED_FILES:
                return

            msg: str = f"File already exists: {new_path}"
            raise FileExistsError(msg)

        shutil.copyfile(path, new_path)

    elif path.is_dir() and is_path_in_marketplace(path):
        for child in path.iterdir():
            flatten_dir(child, dest)


def write_yaml_to_file(
    content: Mapping[str, Any] | Sequence[Any],
    path: pathlib.Path,
) -> None:
    """Write content into a YAML file.

    Args:
        content: the content to write
        path: the path of the YAML file

    """
    dumped: str = yaml.safe_dump(
        data=content,
        indent=4,
        width=80,
        sort_keys=False,
        allow_unicode=True,
    )
    path.write_text(dumped, encoding="utf-8")


def remove_files_by_suffix_from_dir(dir_: pathlib.Path, suffix: str) -> None:
    """Remove all files with a specific suffix from a directory."""
    for file in dir_.rglob(f"*{suffix}"):
        if file.is_file() and is_path_in_marketplace(file):
            file.unlink(missing_ok=True)
