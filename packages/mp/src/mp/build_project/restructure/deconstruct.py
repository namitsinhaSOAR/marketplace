"""Module for deconstructing a built integration into its source structure.

This module defines a class, `DeconstructIntegration`, which takes a built
integration and reorganizes its files and metadata into a structure
suitable for development and modification. This involves separating
scripts, definitions, and other related files into designated directories.
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

import dataclasses
import shutil
import tomllib
from typing import TYPE_CHECKING, Any, TypeAlias

import rich
import toml

import mp.core
import mp.core.constants
import mp.core.file_utils
import mp.core.unix
from mp.core.data_models.action.metadata import ActionMetadata
from mp.core.data_models.connector.metadata import ConnectorMetadata
from mp.core.data_models.integration_meta.metadata import IntegrationMetadata, PythonVersion
from mp.core.data_models.job.metadata import JobMetadata
from mp.core.data_models.widget.metadata import WidgetMetadata

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Mapping, MutableMapping

    from mp.core.data_models.custom_families.metadata import NonBuiltCustomFamily
    from mp.core.data_models.integration import Integration
    from mp.core.data_models.mapping_rules.metadata import NonBuiltMappingRule

_ValidMetadata: TypeAlias = ActionMetadata | ConnectorMetadata | JobMetadata | WidgetMetadata


def _update_pyproject_from_integration_meta(
    pyproject_toml: MutableMapping[str, Any],
    integration_meta: IntegrationMetadata,
) -> None:
    py_version: str = PythonVersion(integration_meta.python_version).to_string()
    pyproject_toml["project"].update(
        {
            "name": integration_meta.identifier.replace(" ", "-"),
            "description": integration_meta.description,
            "version": str(float(integration_meta.version)),
            "requires-python": f">={py_version}",
        },
    )


@dataclasses.dataclass(slots=True, frozen=True)
class DeconstructIntegration:
    path: pathlib.Path
    out_path: pathlib.Path
    integration: Integration

    def _create_resource_files(self) -> None:
        """Create the image files in the resources directory."""
        resources_dir = self.out_path / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Write the PNG file
        if self.integration.metadata.image_base64:
            mp.core.file_utils.base64_to_png_file(
                self.integration.metadata.image_base64, resources_dir / "image.png"
            )

        # Write the SVG file
        if self.integration.metadata.svg_image:
            mp.core.file_utils.text_to_svg_file(
                self.integration.metadata.svg_image, resources_dir / "integration.svg"
            )

    def initiate_project(self) -> None:
        """Initialize a new python project.

        Initializes a project by setting up a Python environment, updating the
        project configuration, and optionally adding dependencies based on a
        'requirements.txt' file.

        """
        mp.core.unix.init_python_project_if_not_exists(self.out_path)
        self.update_pyproject()
        requirements: pathlib.Path = self.path / mp.core.constants.REQUIREMENTS_FILE
        if requirements.exists():
            try:
                rich.print(f"Adding requirements to {mp.core.constants.PROJECT_FILE}")
                mp.core.unix.add_dependencies_to_toml(
                    project_path=self.out_path,
                    requirements_path=requirements,
                )
            except mp.core.unix.FatalCommandError as e:
                rich.print(f"Failed to install dependencies from requirements: {e}")

    def update_pyproject(self) -> None:
        """Update an integration's pyproject.toml file from its definition file."""
        pyproject_toml: pathlib.Path = self.out_path / mp.core.constants.PROJECT_FILE
        toml_content: MutableMapping[str, Any] = tomllib.loads(
            pyproject_toml.read_text(encoding="utf-8"),
        )
        _update_pyproject_from_integration_meta(toml_content, self.integration.metadata)
        pyproject_toml.write_text(toml.dumps(toml_content), encoding="utf-8")
        self._copy_lock_file()

    def _copy_lock_file(self) -> None:
        lock_file: pathlib.Path = self.path / mp.core.constants.LOCK_FILE
        out_lock_file: pathlib.Path = self.out_path / mp.core.constants.LOCK_FILE
        if lock_file.exists() and not out_lock_file.exists():
            shutil.copyfile(lock_file, out_lock_file)

    def deconstruct_integration_files(self) -> None:
        """Deconstruct an integration's code to its "out" path."""
        self._create_resource_files()
        self._create_definition_file()
        self._create_release_notes()
        self._create_custom_families()
        self._create_mapping_rules()
        self._create_scripts_dirs()
        self._create_package_file()

    def _create_definition_file(self) -> None:
        def_file: pathlib.Path = self.out_path / mp.core.constants.DEFINITION_FILE
        mp.core.file_utils.write_yaml_to_file(
            content=self.integration.metadata.to_non_built(),
            path=def_file,
        )

    def _create_release_notes(self) -> None:
        rn: pathlib.Path = self.out_path / mp.core.constants.RELEASE_NOTES_FILE
        mp.core.file_utils.write_yaml_to_file(
            content=[r.to_non_built() for r in self.integration.release_notes],
            path=rn,
        )

    def _create_custom_families(self) -> None:
        cf: pathlib.Path = self.out_path / mp.core.constants.CUSTOM_FAMILIES_FILE
        families: list[NonBuiltCustomFamily] = [
            c.to_non_built() for c in self.integration.custom_families
        ]
        if families:
            mp.core.file_utils.write_yaml_to_file(families, cf)

    def _create_mapping_rules(self) -> None:
        mr: pathlib.Path = self.out_path / mp.core.constants.MAPPING_RULES_FILE
        mapping: list[NonBuiltMappingRule] = [
            m.to_non_built() for m in self.integration.mapping_rules
        ]
        if mapping:
            mp.core.file_utils.write_yaml_to_file(mapping, mr)

    def _create_scripts_dirs(self) -> None:
        self._create_scripts_dir(
            repo_dir=mp.core.constants.OUT_ACTION_SCRIPTS_DIR,
            out_dir=mp.core.constants.ACTIONS_DIR,
            metadata=self.integration.actions_metadata,
        )
        self._create_scripts_dir(
            repo_dir=mp.core.constants.OUT_CONNECTOR_SCRIPTS_DIR,
            out_dir=mp.core.constants.CONNECTORS_DIR,
            metadata=self.integration.connectors_metadata,
        )
        self._create_scripts_dir(
            repo_dir=mp.core.constants.OUT_JOB_SCRIPTS_DIR,
            out_dir=mp.core.constants.JOBS_DIR,
            metadata=self.integration.jobs_metadata,
        )
        self._create_scripts_dir(
            repo_dir=mp.core.constants.OUT_WIDGET_SCRIPTS_DIR,
            out_dir=mp.core.constants.WIDGETS_DIR,
            metadata=self.integration.widgets_metadata,
            is_python_dir=False,
        )
        self._create_scripts_dir(
            repo_dir=mp.core.constants.OUT_MANAGERS_SCRIPTS_DIR,
            out_dir=mp.core.constants.CORE_SCRIPTS_DIR,
            metadata=None,
        )

    def _create_scripts_dir(
        self,
        repo_dir: str,
        out_dir: str,
        metadata: Mapping[str, _ValidMetadata] | None,
        *,
        is_python_dir: bool = True,
    ) -> None:
        old_path: pathlib.Path = self.path / repo_dir
        if not old_path.exists():
            return

        new_path: pathlib.Path = self.out_path / out_dir
        new_path.mkdir(exist_ok=True)
        for file in old_path.iterdir():
            shutil.copy(file, new_path)
            copied_file: pathlib.Path = new_path / file.name
            copied_file.rename(copied_file.parent / copied_file.name)

        if metadata is not None:
            _write_definitions(new_path, metadata)

        if is_python_dir:
            (new_path / mp.core.constants.PACKAGE_FILE).touch()

    def _create_package_file(self) -> None:
        (self.out_path / mp.core.constants.PACKAGE_FILE).touch()


def _write_definitions(
    path: pathlib.Path,
    component: Mapping[str, _ValidMetadata],
) -> None:
    for file_name, metadata in component.items():
        name: str = f"{file_name}{mp.core.constants.DEF_FILE_SUFFIX}"
        mp.core.file_utils.write_yaml_to_file(metadata.to_non_built(), path / name)
