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

import mp.core.constants
import mp.core.data_models.abc
import mp.core.utils

if TYPE_CHECKING:
    import pathlib


class BuiltReleaseNote(mp.core.data_models.abc.BaseBuiltTypedDict):
    ChangeDescription: str
    Deprecated: bool
    New: bool
    ItemName: str
    ItemType: str
    PublishTime: int | None
    Regressive: bool
    Removed: bool
    TicketNumber: str | None
    IntroducedInIntegrationVersion: float


class NonBuiltReleaseNote(mp.core.data_models.abc.BaseNonBuiltTypedDict):
    description: str
    deprecated: bool
    integration_version: float
    item_name: str
    item_type: str
    publish_time: NotRequired[int]
    regressive: bool
    removed: bool
    ticket_number: NotRequired[str]
    new: bool


@dataclasses.dataclass(slots=True, frozen=True)
class ReleaseNote(
    mp.core.data_models.abc.SequentialMetadata[BuiltReleaseNote, NonBuiltReleaseNote],
):
    description: str
    deprecated: bool
    new: bool
    item_name: str
    item_type: str
    publish_time: int | None
    regressive: bool
    removed: bool
    ticket: str | None
    version: float

    @classmethod
    def from_built_integration_path(cls, path: pathlib.Path) -> list[ReleaseNote]:
        """Create based on the metadata files found in the built-integration path.

        Args:
            path: the path to the built integration

        Returns:
            A sequence of `ReleaseNote` objects

        """
        rn_path: pathlib.Path = path / mp.core.constants.RN_JSON_FILE
        if not rn_path.exists():
            return []

        return cls._from_built_integration_path(rn_path)

    @classmethod
    def from_non_built_integration_path(cls, path: pathlib.Path) -> list[ReleaseNote]:
        """Create based on the metadata files found in the non-built-integration path.

        Args:
            path: the path to the non-built integration

        Returns:
            A sequence of `ReleaseNote` objects

        """
        rn_path: pathlib.Path = path / mp.core.constants.RELEASE_NOTES_FILE
        if not rn_path.exists():
            return []

        return cls._from_non_built_integration_path(rn_path)

    @classmethod
    def _from_built(cls, built: BuiltReleaseNote) -> ReleaseNote:
        return cls(
            description=built["ChangeDescription"],
            deprecated=built["Deprecated"],
            version=built["IntroducedInIntegrationVersion"],
            item_name=built["ItemName"],
            item_type=built["ItemType"],
            new=built["New"],
            regressive=built["Regressive"],
            removed=built["Removed"],
            ticket=built["TicketNumber"],
            publish_time=built.get("PublishTime"),
        )

    @classmethod
    def _from_non_built(cls, non_built: NonBuiltReleaseNote) -> ReleaseNote:
        return cls(
            description=non_built["description"],
            deprecated=non_built["deprecated"],
            version=non_built["integration_version"],
            item_name=non_built["item_name"],
            item_type=non_built["item_type"],
            new=non_built["new"],
            regressive=non_built["regressive"],
            removed=non_built["removed"],
            ticket=non_built.get("ticket_number"),
            publish_time=non_built.get("publish_time"),
        )

    def to_built(self) -> BuiltReleaseNote:
        """Create a built release note metadata dict.

        Returns:
            A built version of the release note metadata dict

        """
        return {
            "ChangeDescription": self.description,
            "Deprecated": self.deprecated,
            "IntroducedInIntegrationVersion": self.version,
            "ItemName": self.item_name,
            "ItemType": self.item_type,
            "New": self.new,
            "Regressive": self.regressive,
            "Removed": self.removed,
            "TicketNumber": self.ticket,
            "PublishTime": self.publish_time,
        }

    def to_non_built(self) -> NonBuiltReleaseNote:
        """Create a non-built release note metadata dict.

        Returns:
            A non-built version of the release note metadata dict

        """
        return mp.core.utils.copy_mapping_without_none_values(  # type: ignore[return-value]
            {
                "description": self.description,
                "integration_version": self.version,
                "item_name": self.item_name,
                "item_type": self.item_type,
                "publish_time": self.publish_time,
                "ticket_number": self.ticket,
                "new": self.new,
                "regressive": self.regressive,
                "deprecated": self.deprecated,
                "removed": self.removed,
            },
        )
