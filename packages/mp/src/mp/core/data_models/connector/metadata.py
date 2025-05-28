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
from typing import TYPE_CHECKING, NotRequired, Self

import mp.core.constants
import mp.core.data_models.abc

from .parameter import (
    BuiltConnectorParameter,
    ConnectorParameter,
    NonBuiltConnectorParameter,
)
from .rule import BuiltConnectorRule, ConnectorRule, NonBuiltConnectorRule

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


class BuiltConnectorMetadata(mp.core.data_models.abc.BaseBuiltTypedDict):
    Creator: str
    Description: str
    DocumentationLink: str
    Integration: str
    IsConnectorRulesSupported: bool
    IsCustom: bool
    IsEnabled: bool
    Name: str
    Parameters: Sequence[BuiltConnectorParameter]
    Rules: Sequence[BuiltConnectorRule]
    Version: float


class NonBuiltConnectorMetadata(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    creator: str
    description: str
    documentation_link: str
    integration: str
    is_connector_rules_supported: bool
    is_custom: NotRequired[bool]
    is_enabled: NotRequired[bool]
    name: str
    parameters: Sequence[NonBuiltConnectorParameter]
    rules: Sequence[NonBuiltConnectorRule]
    version: NotRequired[float]


@dataclasses.dataclass(slots=True, frozen=True)
class ConnectorMetadata(
    mp.core.data_models.abc.ScriptMetadata[
        BuiltConnectorMetadata,
        NonBuiltConnectorMetadata,
    ],
):
    file_name: str
    creator: str
    description: str
    documentation_link: str
    integration: str
    is_connector_rules_supported: bool
    is_custom: bool
    is_enabled: bool
    name: str
    parameters: Sequence[
        mp.core.data_models.abc.Buildable[
            BuiltConnectorParameter,
            NonBuiltConnectorParameter,
        ]
    ]
    rules: Sequence[
        mp.core.data_models.abc.Buildable[BuiltConnectorRule, NonBuiltConnectorRule]
    ]
    version: float

    @classmethod
    def from_built_integration_path(cls, path: pathlib.Path) -> list[Self]:
        """Create based on the metadata files found in the built-integration path.

        Args:
            path: the path to the built integration

        Returns:
            A sequence of `ConnectorMetadata` objects

        """
        meta_path: pathlib.Path = path / mp.core.constants.OUT_CONNECTORS_META_DIR
        if not meta_path.exists():
            return []

        return [
            cls._from_built_integration_path(p)
            for p in meta_path.rglob(f"*{mp.core.constants.CONNECTORS_META_SUFFIX}")
        ]

    @classmethod
    def from_non_built_integration_path(cls, path: pathlib.Path) -> list[Self]:
        """Create based on the metadata files found in the non-built-integration path.

        Args:
            path: the path to the non-built integration

        Returns:
            A sequence of `ConnectorMetadata` objects

        """
        meta_path: pathlib.Path = path / mp.core.constants.CONNECTORS_DIR
        if not meta_path.exists():
            return []

        return [
            cls._from_non_built_integration_path(p)
            for p in meta_path.rglob(f"*{mp.core.constants.DEF_FILE_SUFFIX}")
        ]

    @classmethod
    def _from_built(
        cls,
        file_name: str,
        built: BuiltConnectorMetadata,
    ) -> ConnectorMetadata:
        return cls(
            file_name=file_name,
            creator=built["Creator"],
            description=built["Description"],
            documentation_link=built["DocumentationLink"],
            integration=built["Integration"],
            is_connector_rules_supported=built["IsConnectorRulesSupported"],
            is_custom=built["IsCustom"],
            is_enabled=built["IsEnabled"],
            name=built["Name"],
            parameters=[
                ConnectorParameter.from_built(param) for param in built["Parameters"]
            ],
            rules=[ConnectorRule.from_built(rule) for rule in built["Rules"]],
            version=built.get("Version", 1.0),
        )

    @classmethod
    def _from_non_built(
        cls,
        file_name: str,
        non_built: NonBuiltConnectorMetadata,
    ) -> ConnectorMetadata:
        return cls(
            file_name=file_name,
            creator=non_built["creator"],
            description=non_built["description"],
            documentation_link=non_built["documentation_link"],
            integration=non_built["integration"],
            is_connector_rules_supported=non_built["is_connector_rules_supported"],
            is_custom=non_built.get("is_custom", False),
            is_enabled=non_built.get("is_enabled", True),
            name=non_built["name"],
            parameters=[
                ConnectorParameter.from_non_built(param)
                for param in non_built["parameters"]
            ],
            rules=[ConnectorRule.from_non_built(rule) for rule in non_built["rules"]],
            version=non_built.get("version", 1.0),
        )

    def to_built(self) -> BuiltConnectorMetadata:
        """Create a built connector metadata dict.

        Returns:
            A built version of the connector metadata dict

        """
        return {
            "Creator": self.creator,
            "Description": self.description,
            "DocumentationLink": self.documentation_link,
            "Integration": self.integration,
            "IsConnectorRulesSupported": self.is_connector_rules_supported,
            "IsCustom": self.is_custom,
            "IsEnabled": self.is_enabled,
            "Name": self.name,
            "Parameters": [param.to_built() for param in self.parameters],
            "Rules": [rule.to_built() for rule in self.rules],
            "Version": self.version,
        }

    def to_non_built(self) -> NonBuiltConnectorMetadata:
        """Create a non-built connector metadata dict.

        Returns:
            A non-built version of the connector metadata dict

        """
        return {
            "name": self.name,
            "parameters": [param.to_non_built() for param in self.parameters],
            "description": self.description,
            "integration": self.integration,
            "documentation_link": self.documentation_link,
            "rules": [rule.to_non_built() for rule in self.rules],
            "is_connector_rules_supported": self.is_connector_rules_supported,
            "creator": self.creator,
        }
