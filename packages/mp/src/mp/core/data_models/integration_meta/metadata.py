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
import json
from typing import TYPE_CHECKING, NotRequired, Self

import yaml

import mp.core.constants
import mp.core.data_models.abc
import mp.core.utils

from .feature_tags import BuiltFeatureTags, FeatureTags, NonBuiltFeatureTags
from .parameter import (
    BuiltIntegrationParameter,
    IntegrationParameter,
    NonBuiltIntegrationParameter,
)

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


class PythonVersion(mp.core.data_models.abc.RepresentableEnum):
    PY_3_7 = 2
    PY_3_11 = 3

    @classmethod
    def from_string(cls, s: str, /) -> PythonVersion:
        """Create PythonVersion from string representation.

        Returns:
            The PythonVersion object

        """
        str_to_enum: dict[str, PythonVersion] = {
            "3.7": cls.PY_3_7,
            "3.11": cls.PY_3_11,
        }
        return str_to_enum[str(s)]

    def to_string(self) -> str:
        """PythonVersion's string representation.

        Returns:
            A string representation of the object

        """
        enum_to_str: dict[PythonVersion, str] = {
            PythonVersion.PY_3_7: "3.7",
            PythonVersion.PY_3_11: "3.11",
        }
        return enum_to_str[self]


class BuiltIntegrationMetadata(mp.core.data_models.abc.BaseBuiltTypedDict):
    Categories: Sequence[str]
    Description: str
    FeatureTags: NotRequired[BuiltFeatureTags]
    DisplayName: str
    Identifier: str
    PythonVersion: int
    DocumentationLink: str | None
    ImageBase64: str
    IntegrationProperties: Sequence[BuiltIntegrationParameter]
    ShouldInstalledInSystem: bool
    IsAvailableForCommunity: bool
    MarketingDisplayName: str
    MinimumSystemVersion: float
    SVGImage: str
    SvgImage: NotRequired[str]
    Version: float
    IsCustom: bool
    IsPowerUp: bool


class NonBuiltIntegrationMetadata(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    categories: Sequence[str]
    description: str
    feature_tags: NotRequired[NonBuiltFeatureTags]
    name: str
    identifier: str
    python_version: str
    documentation_link: NotRequired[str | None]
    image_base64: str
    parameters: Sequence[NonBuiltIntegrationParameter]
    should_install_in_system: NotRequired[bool]
    svg_image: str | None
    version: float
    is_custom: NotRequired[bool]
    is_available_for_community: NotRequired[bool]
    is_powerup: NotRequired[bool]


@dataclasses.dataclass(slots=True)
class IntegrationMetadata(
    mp.core.data_models.abc.Buildable[
        BuiltIntegrationMetadata,
        NonBuiltIntegrationMetadata,
    ],
):
    categories: Sequence[str]
    description: str
    feature_tags: (
        mp.core.data_models.abc.Buildable[BuiltFeatureTags, NonBuiltFeatureTags] | None
    )
    name: str
    identifier: str
    python_version: PythonVersion
    documentation_link: str | None
    image_base64: str
    parameters: Sequence[
        mp.core.data_models.abc.Buildable[
            BuiltIntegrationParameter,
            NonBuiltIntegrationParameter,
        ]
    ]
    should_install_in_system: bool
    svg_image: str | None
    version: float
    is_custom: bool
    is_available_for_community: bool
    is_powerup: bool
    minimum_system_version: float = mp.core.constants.MINIMUM_SYSTEM_VERSION

    @classmethod
    def from_built_integration_path(cls, path: pathlib.Path) -> Self:
        """Create IntegrationMetadata from a path of a "built" integration.

        Args:
            path: the path to the integration's "built" version

        Returns:
            An IntegrationMetadata object

        Raises:
            ValueError: when the "built" is failed to be loaded

        """
        metadata_file: str = mp.core.constants.INTEGRATION_DEF_FILE.format(path.name)
        metadata_path: pathlib.Path = path / metadata_file
        built: str = metadata_path.read_text(encoding="utf-8")
        try:
            metadata_content: BuiltIntegrationMetadata = json.loads(built)
            metadata: Self = cls.from_built(metadata_content)
        except (ValueError, json.JSONDecodeError) as e:
            msg: str = f"Failed to load json from {metadata_path}\n{built}"
            raise ValueError(msg) from e
        else:
            return metadata

    @classmethod
    def from_non_built_integration_path(cls, path: pathlib.Path) -> Self:
        """Create IntegrationMetadata from a path of a "non-built" integration.

        Args:
            path: the path to the integration's "non-built" version

        Returns:
            An IntegrationMetadata object

        Raises:
            ValueError: when the "non-built" is failed to be loaded

        """
        metadata_path: pathlib.Path = path / mp.core.constants.DEFINITION_FILE
        built: str = metadata_path.read_text(encoding="utf-8")
        try:
            metadata_content: NonBuiltIntegrationMetadata = yaml.safe_load(built)
            metadata: Self = cls.from_non_built(metadata_content)
        except (ValueError, json.JSONDecodeError) as e:
            msg: str = f"Failed to load json from {metadata_path}\n{built}"
            raise ValueError(msg) from e
        else:
            return metadata

    @classmethod
    def _from_built(cls, built: BuiltIntegrationMetadata) -> Self:
        feature_tags: (
            mp.core.data_models.abc.Buildable[BuiltFeatureTags, NonBuiltFeatureTags]
            | None
        ) = None
        raw_feature_tags: BuiltFeatureTags | None = built.get("FeatureTags")
        if raw_feature_tags is not None:
            feature_tags = FeatureTags.from_built(raw_feature_tags)

        return cls(
            categories=built["Categories"],
            description=built["Description"],
            feature_tags=feature_tags,
            name=built["DisplayName"],
            identifier=built["Identifier"],
            python_version=PythonVersion(built["PythonVersion"]),
            documentation_link=built["DocumentationLink"],
            image_base64=built["ImageBase64"],
            parameters=[
                IntegrationParameter.from_built(p)
                for p in built["IntegrationProperties"]
            ],
            should_install_in_system=built["ShouldInstalledInSystem"],
            svg_image=built.get("SVGImage", built.get("SvgImage")),
            version=built["Version"],
            is_custom=built.get("IsCustom", False),
            is_available_for_community=built.get("IsAvailableForCommunity", True),
            is_powerup=built.get("IsPowerUp", False),
        )

    @classmethod
    def _from_non_built(cls, non_built: NonBuiltIntegrationMetadata) -> Self:
        feature_tags: (
            mp.core.data_models.abc.Buildable[BuiltFeatureTags, NonBuiltFeatureTags]
            | None
        ) = None
        raw_feature_tags: NonBuiltFeatureTags | None = non_built.get("feature_tags")
        if raw_feature_tags is not None:
            feature_tags = FeatureTags.from_non_built(raw_feature_tags)

        return cls(
            categories=non_built["categories"],
            description=non_built["description"],
            feature_tags=feature_tags,
            name=non_built["name"],
            identifier=non_built["identifier"],
            python_version=PythonVersion.from_string(non_built["python_version"]),
            documentation_link=non_built.get("documentation_link"),
            image_base64=non_built["image_base64"],
            parameters=[
                IntegrationParameter.from_non_built(p) for p in non_built["parameters"]
            ],
            should_install_in_system=non_built.get("should_install_in_system", False),
            is_custom=non_built.get("is_custom", False),
            svg_image=non_built.get("svg_image"),
            version=non_built["version"],
            is_available_for_community=non_built.get(
                "is_available_for_community",
                True,
            ),
            is_powerup=non_built.get("is_powerup", False),
        )

    def to_built(self) -> BuiltIntegrationMetadata:
        """Create the "built" TypedDict version of the integration's metadata.

        Returns:
            The "built" TypedDict version of the integration's metadata.

        """
        return mp.core.utils.copy_mapping_without_none_values(  # type: ignore[return-value]
            {
                "Categories": self.categories,
                "Description": self.description,
                "DisplayName": self.name,
                "DocumentationLink": self.documentation_link,
                "FeatureTags": (
                    self.feature_tags.to_built()
                    if self.feature_tags is not None
                    else None
                ),
                "Identifier": self.identifier,
                "ImageBase64": self.image_base64,
                "IntegrationProperties": [p.to_built() for p in self.parameters],
                "IsAvailableForCommunity": True,
                "MarketingDisplayName": self.name,
                "MinimumSystemVersion": self.minimum_system_version,
                "PythonVersion": self.python_version.value,
                "SVGImage": self.svg_image,
                "ShouldInstalledInSystem": self.should_install_in_system,
                "Version": self.version,
                "IsCustom": self.is_custom,
                "IsPowerUp": self.is_powerup,
            },
        )

    def to_non_built(self) -> NonBuiltIntegrationMetadata:
        """Create the "non-built" TypedDict version of the integration's metadata.

        Returns:
            The "non-built" TypedDict version of the integration's metadata.

        """
        non_built: NonBuiltIntegrationMetadata = {
            "identifier": self.identifier,
            "name": self.name,
            "version": self.version,
            "parameters": [p.to_non_built() for p in self.parameters],
            "description": self.description,
            "python_version": self.python_version.to_string(),
            "documentation_link": self.documentation_link,
            "categories": self.categories,
            "svg_image": self.svg_image,
            "image_base64": self.image_base64,
        }

        if self.feature_tags is not None:
            non_built["feature_tags"] = self.feature_tags.to_non_built()

        if self.should_install_in_system is True:
            non_built["should_install_in_system"] = self.should_install_in_system

        if self.is_available_for_community is False:
            non_built["is_available_for_community"] = self.is_available_for_community

        if self.is_powerup is True:
            non_built["is_powerup"] = self.is_powerup

        return mp.core.utils.copy_mapping_without_none_values(non_built)  # type: ignore[return-value]
