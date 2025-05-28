"""Core logic for building and deconstructing integration marketplaces.

This module defines the `Marketplace` class, which provides the functionality
to build and deconstruct integrations and groups of integrations within a
marketplace directory. It orchestrates the process of reading integration
definitions, restructuring their components, and generating the final
marketplace JSON file. It also handles the reverse process of deconstructing
built integrations back into their source structure.
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

import multiprocessing
import shutil
from typing import TYPE_CHECKING

import rich

import mp.core.config
import mp.core.constants
import mp.core.file_utilities as futils
import mp.core.unix
import mp.core.utils
from mp.core.data_models.integration import (
    BuiltFullDetails,
    BuiltIntegration,
    Integration,
)

from .post_build.full_details_json import write_full_details
from .post_build.marketplace_json import write_marketplace_json
from .restructure.deconstruct import DeconstructIntegration, update_pyproject
from .restructure.integration import restructure_integration

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterable, Iterator

    from mp.core.custom_types import Products


class Marketplace:
    def __init__(self, integrations_dir: pathlib.Path) -> None:
        """Class constructor.

        Args:
            integrations_dir: The path to a marketplace - where folders of integrations
                and groups exist

        """
        self.path: pathlib.Path = integrations_dir
        self.path.mkdir(exist_ok=True)

        mp_path: pathlib.Path = mp.core.config.get_marketplace_path()
        out_path: pathlib.Path = mp_path / mp.core.constants.OUT_DIR_NAME
        out_path.mkdir(exist_ok=True)

        self.out_path: pathlib.Path = (
            out_path / mp.core.constants.OUT_INTEGRATIONS_DIR_NAME
        )
        self.out_path.mkdir(exist_ok=True)

        self.out_path /= integrations_dir.name
        self.out_path.mkdir(exist_ok=True)

    def write_marketplace_json(self) -> None:
        """Write the marketplace JSON file to the marketplace's out path."""
        write_marketplace_json(self.out_path)

    def build(self) -> None:
        """Build all integrations and groups in the marketplace."""
        products: Products[set[pathlib.Path]] = (
            futils.get_integrations_and_groups_from_paths(self.path)
        )
        self.build_groups(products.groups)
        self.build_integrations(products.integrations)

    def build_groups(self, group_paths: Iterable[pathlib.Path]) -> None:
        """Build all groups provided by `group_paths`.

        Args:
            group_paths: The paths of integrations to build

        """
        with multiprocessing.Pool(
            processes=mp.core.config.get_processes_number(),
        ) as pool:
            pool.map(self.build_group, group_paths)

    def build_group(self, group_dir: pathlib.Path) -> None:
        """Build a single group provided by `group_path`.

        Args:
            group_dir: The paths of the integration to build

        Raises:
            FileNotFoundError: when `group_dir` does not exist

        """
        if not group_dir.exists():
            msg: str = f"Invalid integration {group_dir}"
            raise FileNotFoundError(msg)

        self.build_integrations(group_dir.iterdir())

    def build_integrations(self, integration_paths: Iterable[pathlib.Path]) -> None:
        """Build all integrations provided by `integration_paths`.

        Args:
            integration_paths: The paths of integrations to build

        """
        paths: Iterator[pathlib.Path] = (
            p for p in integration_paths if p.exists() and futils.is_integration(p)
        )
        with multiprocessing.Pool(
            processes=mp.core.config.get_processes_number(),
        ) as pool:
            pool.map(self.build_integration, paths)

    def build_integration(self, integration_path: pathlib.Path) -> None:
        """Build a single integration provided by `integration_path`.

        Args:
            integration_path: The paths of the integration to build

        Raises:
            FileNotFoundError: when `integration_path` does not exist

        """
        if not integration_path.exists():
            msg: str = f"Invalid integration {integration_path}"
            raise FileNotFoundError(msg)

        integration: Integration
        if futils.is_built(integration_path) or futils.is_half_built(integration_path):
            rich.print(f"Integration {integration_path.name} is built")
            futils.remove_and_create_dir(self.out_path / integration_path.name)
            shutil.copytree(
                src=integration_path,
                dst=self.out_path / integration_path.name,
                dirs_exist_ok=True,
            )
            integration = Integration.from_built_path(integration_path)

        else:
            rich.print(f"Integration {integration_path.name} is not built")
            integration = Integration.from_non_built_path(integration_path)
            futils.remove_and_create_dir(self.out_path / integration.identifier)

        self._build_integration(integration, integration_path)

        rich.print("Removing project files from out path")
        self._remove_project_files_from_built_out_path(integration.identifier)

    def _build_integration(
        self,
        integration: Integration,
        integration_path: pathlib.Path,
    ) -> None:
        rich.print(f"---------- Building {integration_path.stem} ----------")
        integration_out_path: pathlib.Path = self.out_path / integration.identifier
        integration_out_path.mkdir(exist_ok=True)

        built: BuiltIntegration = integration.to_built()
        restructure_integration(built, integration_path, integration_out_path)

        full_details: BuiltFullDetails = integration.to_built_full_details()
        write_full_details(full_details, integration_out_path)

    def _remove_project_files_from_built_out_path(self, integration_id: str) -> None:
        self._remove_project_files_from_out_path(integration_id)
        integration: pathlib.Path = self.out_path / integration_id
        futils.remove_paths_if_exists(
            integration / mp.core.constants.PROJECT_FILE,
            integration / mp.core.constants.LOCK_FILE,
            integration / mp.core.constants.ACTIONS_DIR,
            integration / mp.core.constants.CONNECTORS_DIR,
            integration / mp.core.constants.JOBS_DIR,
            integration / mp.core.constants.WIDGETS_DIR,
            integration / mp.core.constants.RELEASE_NOTES_FILE,
            integration / mp.core.constants.DEFINITION_FILE,
            integration / mp.core.constants.MAPPING_RULES_FILE,
            integration / mp.core.constants.CUSTOM_FAMILIES_FILE,
            integration / mp.core.constants.PACKAGE_FILE,
            integration
            / mp.core.constants.OUT_ACTION_SCRIPTS_DIR
            / mp.core.constants.PACKAGE_FILE,
            integration
            / mp.core.constants.OUT_CONNECTOR_SCRIPTS_DIR
            / mp.core.constants.PACKAGE_FILE,
            integration
            / mp.core.constants.OUT_JOB_SCRIPTS_DIR
            / mp.core.constants.PACKAGE_FILE,
            integration
            / mp.core.constants.OUT_MANAGERS_SCRIPTS_DIR
            / mp.core.constants.PACKAGE_FILE,
        )

    def deconstruct_integrations(
        self,
        integration_paths: Iterable[pathlib.Path],
    ) -> None:
        """Deconstruct all integrations provided by `integration_paths`.

        Args:
            integration_paths: The paths of integrations to deconstruct

        """
        paths: Iterator[pathlib.Path] = (
            p for p in integration_paths if p.exists() and futils.is_integration(p)
        )
        with multiprocessing.Pool(
            processes=mp.core.config.get_processes_number(),
        ) as pool:
            pool.map(self.deconstruct_integration, paths)

    def deconstruct_integration(self, integration_path: pathlib.Path) -> None:
        """Deconstruct a single integration provided by `integration_path`.

        Args:
            integration_path: The paths of the integration to deconstruct

        Raises:
            FileNotFoundError: when `integration_path` does not exist

        """
        rich.print(f"---------- Deconstructing {integration_path.stem} ----------")
        if not integration_path.exists():
            msg: str = f"Invalid integration {integration_path}"
            raise FileNotFoundError(msg)

        integration_out_path: pathlib.Path = (
            self.out_path
            / mp.core.utils.str_to_snake_case(
                integration_path.name,
            )
        )
        futils.remove_and_create_dir(integration_out_path)
        shutil.copytree(
            src=integration_path,
            dst=integration_out_path,
            dirs_exist_ok=True,
        )
        integration: Integration
        if futils.is_built(integration_path) or futils.is_half_built(integration_path):
            rich.print(f"Integration {integration_path.name} is built")
            integration = Integration.from_built_path(integration_path)
            self._deconstruct_integration(integration, integration_path)

        else:
            integration = Integration.from_non_built_path(integration_path)

        rich.print(f"Creating {mp.core.constants.DEFINITION_FILE}")
        di: DeconstructIntegration = DeconstructIntegration(
            out_path=integration_out_path,
            path=integration_path,
            integration=integration,
        )
        di.deconstruct_integration_files()

        rich.print("Removing project files from out path")
        self._remove_project_files_from_non_built_out_path(
            integration_name=mp.core.utils.str_to_snake_case(integration_path.name),
            integration_original_name=integration_path.name,
        )

    def _deconstruct_integration(
        self,
        integration: Integration,
        integration_path: pathlib.Path,
    ) -> None:
        integration_out_path: pathlib.Path = (
            self.out_path
            / mp.core.utils.str_to_snake_case(
                integration_path.name,
            )
        )
        proj: pathlib.Path = integration_path / mp.core.constants.PROJECT_FILE
        if proj.exists():
            shutil.copyfile(proj, integration_out_path / mp.core.constants.PROJECT_FILE)
            rich.print(f"Updating {mp.core.constants.PROJECT_FILE}")
            update_pyproject(integration_out_path, integration)
            return

        mp.core.unix.init_python_project_if_not_exists(integration_out_path)
        rich.print(f"Updating {mp.core.constants.PROJECT_FILE}")
        update_pyproject(integration_out_path, integration)
        requirements: pathlib.Path = (
            integration_path / mp.core.constants.REQUIREMENTS_FILE
        )
        if requirements.exists():
            try:
                rich.print(f"Adding requirements to {mp.core.constants.PROJECT_FILE}")
                mp.core.unix.add_dependencies_to_toml(
                    project_path=integration_out_path,
                    requirements_path=requirements,
                )
            except mp.core.unix.CommandError as e:
                rich.print(f"Failed to install dependencies from requirements: {e}")

    def _remove_project_files_from_non_built_out_path(
        self,
        integration_name: str,
        integration_original_name: str,
    ) -> None:
        self._remove_project_files_from_out_path(integration_name)
        integration: pathlib.Path = self.out_path / integration_name
        futils.remove_paths_if_exists(
            integration / mp.core.constants.OUT_DEPENDENCIES_DIR,
            integration / mp.core.constants.OUT_ACTIONS_META_DIR,
            integration / mp.core.constants.OUT_CONNECTORS_META_DIR,
            integration / mp.core.constants.OUT_JOBS_META_DIR,
            integration / mp.core.constants.OUT_WIDGETS_META_DIR,
            integration / mp.core.constants.OUT_ACTION_SCRIPTS_DIR,
            integration / mp.core.constants.OUT_CONNECTOR_SCRIPTS_DIR,
            integration / mp.core.constants.OUT_JOB_SCRIPTS_DIR,
            integration / mp.core.constants.OUT_WIDGET_SCRIPTS_DIR,
            integration / mp.core.constants.OUT_CUSTOM_FAMILIES_DIR,
            integration / mp.core.constants.OUT_MAPPING_RULES_DIR,
            integration / mp.core.constants.OUT_MANAGERS_SCRIPTS_DIR,
            integration / mp.core.constants.RN_JSON_FILE,
            integration
            / mp.core.constants.INTEGRATION_DEF_FILE.format(integration_original_name),
            integration
            / mp.core.constants.INTEGRATION_FULLDETAILS_FILE.format(
                integration_original_name,
            ),
        )

    def _remove_project_files_from_out_path(self, integration_name: str) -> None:
        integration: pathlib.Path = self.out_path / integration_name
        futils.remove_paths_if_exists(
            integration / mp.core.constants.REQUIREMENTS_FILE,
            integration / mp.core.constants.PYTHON_VERSION_FILE,
            integration / mp.core.constants.README_FILE,
            integration / mp.core.constants.INTEGRATION_VENV,
            integration / mp.core.constants.TESTS_DIR,
        )
