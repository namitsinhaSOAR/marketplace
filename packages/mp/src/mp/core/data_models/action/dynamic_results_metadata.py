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


class BuiltDynamicResultsMetadata(mp.core.data_models.abc.BaseBuiltTypedDict):
    ResultExample: str
    ResultName: str
    ShowResult: bool


class NonBuiltDynamicResultsMetadata(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    result_example: str
    result_name: str
    show_result: bool


@dataclasses.dataclass(slots=True, frozen=True)
class DynamicResultsMetadata(
    mp.core.data_models.abc.Buildable[
        BuiltDynamicResultsMetadata,
        NonBuiltDynamicResultsMetadata,
    ],
):
    result_example: str
    result_name: str
    show_result: bool

    @classmethod
    def _from_built(cls, built: BuiltDynamicResultsMetadata) -> DynamicResultsMetadata:
        """Create the obj from a built dynamic results metadata dict.

        Args:
            built: the built dict

        Returns:
            A `DynamicResultsMetadata` object

        """
        return cls(
            result_example=built.get("ResultExample", ""),
            result_name=built["ResultName"],
            show_result=built.get("ShowResult", True),
        )

    @classmethod
    def _from_non_built(
        cls,
        non_built: NonBuiltDynamicResultsMetadata,
    ) -> DynamicResultsMetadata:
        """Create the obj from a non-built dynamic results metadata dict.

        Args:
            non_built: the non-built dict

        Returns:
            A `DynamicResultsMetadata` object

        """
        return cls(
            result_example=non_built["result_example"],
            result_name=non_built["result_name"],
            show_result=non_built["show_result"],
        )

    def to_built(self) -> BuiltDynamicResultsMetadata:
        """Create a built dynamic results metadata dict.

        Returns:
            A built version of the dynamic results metadata dict

        """
        return {
            "ResultExample": self.result_example,
            "ResultName": self.result_name,
            "ShowResult": self.show_result,
        }

    def to_non_built(self) -> NonBuiltDynamicResultsMetadata:
        """Create a non-built dynamic results metadata dict.

        Returns:
            A non-built version of the dynamic results metadata dict

        """
        return {
            "result_name": self.result_name,
            "show_result": self.show_result,
            "result_example": self.result_example,
        }
