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

import mp.core.data_models.abc


class MatchType(mp.core.data_models.abc.RepresentableEnum):
    EQUAL = 0
    CONTAINS = 1
    STARTS_WITH = 2
    GREATER_THAN = 3
    LESS_THAN = 3
    NOT_EQUAL = 5
    NOT_CONTAINS = 6
    IS_EMPTY = 7
    IS_NOT_EMPTY = 8


class BuiltCondition(mp.core.data_models.abc.BaseBuiltTypedDict):
    fieldName: str  # noqa: N815
    value: str
    matchType: int  # noqa: N815


class NonBuiltCondition(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    field_name: str
    value: str
    match_type: str


@dataclasses.dataclass(slots=True, frozen=True)
class Condition(mp.core.data_models.abc.Buildable[BuiltCondition, NonBuiltCondition]):
    field_name: str
    value: str
    match_type: MatchType

    @classmethod
    def _from_built(cls, built: BuiltCondition) -> Condition:
        return cls(
            field_name=built["fieldName"],
            value=built["value"],
            match_type=MatchType(built["matchType"]),
        )

    @classmethod
    def _from_non_built(cls, non_built: NonBuiltCondition) -> Condition:
        return cls(
            field_name=non_built["field_name"],
            value=non_built["value"],
            match_type=MatchType.from_string(non_built["match_type"]),
        )

    def to_built(self) -> BuiltCondition:
        """Turn the buildable object into a "built" typed dict.

        Returns:
            The "built" representation of the object.

        """
        return {
            "fieldName": self.field_name,
            "value": self.value,
            "matchType": self.match_type.value,
        }

    def to_non_built(self) -> NonBuiltCondition:
        """Turn the buildable object into a "non-built" typed dict.

        Returns:
            The "non-built" representation of the object

        """
        return {
            "field_name": self.field_name,
            "value": self.value,
            "match_type": self.match_type.to_string(),
        }
