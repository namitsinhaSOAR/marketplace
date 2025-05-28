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
from typing import TYPE_CHECKING

import mp.core.constants
import mp.core.data_models.abc

from .rule import BuiltCustomFamilyRule, CustomFamilyRule, NonBuiltCustomFamilyRule

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Sequence


class BuiltCustomFamily(mp.core.data_models.abc.BaseBuiltTypedDict):
    Family: str
    Description: str
    ImageBase64: str
    IsCustom: bool
    Rules: Sequence[BuiltCustomFamilyRule]


class NonBuiltCustomFamily(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    family: str
    description: str
    image_base64: str
    is_custom: bool
    rules: Sequence[NonBuiltCustomFamilyRule]


@dataclasses.dataclass(slots=True, frozen=True)
class CustomFamily(
    mp.core.data_models.abc.SequentialMetadata[BuiltCustomFamily, NonBuiltCustomFamily],
):
    family: str
    description: str
    image_base64: str
    is_custom: bool
    rules: Sequence[
        mp.core.data_models.abc.Buildable[
            BuiltCustomFamilyRule,
            NonBuiltCustomFamilyRule,
        ]
    ]

    @classmethod
    def from_built_integration_path(cls, path: pathlib.Path) -> list[CustomFamily]:
        """Create based on the metadata files found in the built-integration path.

        Args:
            path: the path to the built integration

        Returns:
            A sequence of `CustomFamily` objects

        """
        meta_path: pathlib.Path = (
            path
            / mp.core.constants.OUT_CUSTOM_FAMILIES_DIR
            / mp.core.constants.OUT_CUSTOM_FAMILIES_FILE
        )
        if not meta_path.exists():
            return []

        return cls._from_built_integration_path(meta_path)

    @classmethod
    def from_non_built_integration_path(cls, path: pathlib.Path) -> list[CustomFamily]:
        """Create based on the metadata files found in the non-built-integration path.

        Args:
            path: the path to the non-built integration

        Returns:
            A sequence of `CustomFamily` objects

        """
        meta_path: pathlib.Path = path / mp.core.constants.CUSTOM_FAMILIES_FILE
        if not meta_path.exists():
            return []

        return cls._from_non_built_integration_path(meta_path)

    @classmethod
    def _from_built(cls, built: BuiltCustomFamily) -> CustomFamily:
        return cls(
            family=built["Family"],
            description=built["Description"],
            image_base64=built["ImageBase64"],
            is_custom=built.get("IsCustom", False),
            rules=[CustomFamilyRule.from_built(rule) for rule in built["Rules"]],
        )

    @classmethod
    def _from_non_built(cls, non_built: NonBuiltCustomFamily) -> CustomFamily:
        return cls(
            family=non_built["family"],
            description=non_built["description"],
            image_base64=non_built["image_base64"],
            is_custom=non_built.get("is_custom", False),
            rules=[
                CustomFamilyRule.from_non_built(rule) for rule in non_built["rules"]
            ],
        )

    def to_built(self) -> BuiltCustomFamily:
        """Create a built custom family metadata dict.

        Returns:
            A built version of the custom family metadata dict

        """
        return {
            "Family": self.family,
            "Description": self.description,
            "ImageBase64": self.image_base64,
            "IsCustom": self.is_custom,
            "Rules": [rule.to_built() for rule in self.rules],
        }

    def to_non_built(self) -> NonBuiltCustomFamily:
        """Create a non-built custom family metadata dict.

        Returns:
            A non-built version of the custom family metadata dict

        """
        return {
            "family": self.family,
            "description": self.description,
            "image_base64": self.image_base64,
            "is_custom": self.is_custom,
            "rules": [rule.to_non_built() for rule in self.rules],
        }
