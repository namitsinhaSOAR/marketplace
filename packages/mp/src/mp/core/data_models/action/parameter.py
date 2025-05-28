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
from typing import TYPE_CHECKING, NotRequired

import mp.core.data_models.abc
import mp.core.utils

if TYPE_CHECKING:
    from collections.abc import Sequence


class ActionParamType(mp.core.data_models.abc.RepresentableEnum):
    STRING = 0
    INTEGER = 0
    BOOLEAN = 1
    PLAYBOOK_NAME = 2
    USER = 3
    STAGE = 4
    CLOSE_CASE_REASONS = 5
    CLOSE_ROOT_CAUSE = 6
    CASE_PRIORITIES = 7
    EMAIL_CONTENT = 10
    CONTENT = 11
    PASSWORD = 12
    ENTITY_TYPE = 13
    MULTI_VALUES = 14
    DDL = 15
    CODE = 16
    TIME_SPAN_SECONDS = 17
    MULTI_CHOICE_PARAMETER = 21
    NULL = -1


class BuiltActionParameter(mp.core.data_models.abc.BaseBuiltTypedDict):
    Description: str
    IsMandatory: bool
    Name: str
    OptionalValues: NotRequired[Sequence[str]]
    Type: int
    Value: str | bool | int | float | None
    DefaultValue: str | bool | int | float | None


class NonBuiltActionParameter(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    description: str
    is_mandatory: bool
    name: str
    optional_values: NotRequired[Sequence[str]]
    type: str
    default_value: NotRequired[str | bool | int | float]


@dataclasses.dataclass(slots=True, frozen=True)
class ActionParameter(
    mp.core.data_models.abc.Buildable[BuiltActionParameter, NonBuiltActionParameter],
):
    description: str
    is_mandatory: bool
    name: str
    optional_values: Sequence[str] | None
    type_: ActionParamType
    value: str | bool | int | float | None

    @classmethod
    def _from_built(cls, built: BuiltActionParameter) -> ActionParameter:
        """Create the obj from a built action param dict.

        Args:
            built: the built dict

        Returns:
            An `ActionParameter` object

        """
        return cls(
            description=built["Description"],
            is_mandatory=built["IsMandatory"],
            name=built["Name"],
            optional_values=built.get("OptionalValues"),
            type_=ActionParamType(int(built["Type"])),
            value=built.get("Value", built.get("DefaultValue")),
        )

    @classmethod
    def _from_non_built(cls, non_built: NonBuiltActionParameter) -> ActionParameter:
        """Create the obj from a non-built action param dict.

        Args:
            non_built: the non-built dict

        Returns:
            An `ActionParameter` object

        """
        return cls(
            description=non_built["description"],
            is_mandatory=non_built["is_mandatory"],
            name=non_built["name"],
            optional_values=non_built.get("optional_values"),
            type_=ActionParamType.from_string(non_built["type"]),
            value=non_built.get("default_value"),
        )

    def to_built(self) -> BuiltActionParameter:
        """Create a built action param dict.

        Returns:
            A built version of the action parameter dict

        """
        results: BuiltActionParameter = {
            "DefaultValue": self.value,
            "Description": self.description,
            "IsMandatory": self.is_mandatory,
            "Name": self.name,
            "Type": self.type_.value,
            "Value": self.value,
        }
        if self.optional_values is not None:
            results["OptionalValues"] = self.optional_values

        return results

    def to_non_built(self) -> NonBuiltActionParameter:
        """Create a non-built action param dict.

        Returns:
            A non-built version of the action parameter dict

        """
        return mp.core.utils.copy_mapping_without_none_values(  # type: ignore[return-value]
            {
                "name": self.name,
                "default_value": self.value,
                "type": self.type_.to_string(),
                "description": self.description,
                "is_mandatory": self.is_mandatory,
            },
        )
