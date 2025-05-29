"""Utilities for generating the marketplace JSON file.

This module provides functionality to traverse integration directories,
read their definition files, and compile them into a comprehensive
`marketplace.json` file. It also includes checks for duplicate
integration identifiers within a marketplace.
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
import json
from typing import TYPE_CHECKING, NamedTuple

import mp.core.constants
import mp.core.file_utils
from mp.core.data_models.connector.metadata import ConnectorMetadata
from mp.core.data_models.release_notes.metadata import ReleaseNote

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterable, Sequence

    from mp.core.custom_types import Products
    from mp.core.data_models.action.metadata import BuiltActionMetadata

    from .data_models import (
        BuiltFullDetailsIntegrationMetadata,
        BuiltSupportedAction,
        FullDetailsExtraAttrs,
    )


MS_IN_SEC: int = 1_000
DAY_IN_MILLISECONDS: int = MS_IN_SEC * 60 * 60 * 24
UPDATE_NOTIFICATIONS_DAYS: int = 4
NEW_NOTIFICATION_DAYS: int = 30


class DuplicateIntegrationIdentifierInMarketplaceError(Exception):
    """When a marketplace (community/commercial) contains duplicate integration IDs."""


class ReleaseTimes(NamedTuple):
    """Release Time parameters."""

    latest_release: int | None
    update_notification: int | None
    new_notification: int | None


def write_marketplace_json(dst: pathlib.Path) -> None:
    """Write the marketplace JSON file to a path.

    Args:
        dst: destination path to write the marketplace JSON into

    Raises:
        DuplicateIntegrationIdentifierInMarketplaceError:
            when multiple integrations with the same name were added to the
            `marketplace.json` file

    """
    products: Products[set[pathlib.Path]] = (
        mp.core.file_utils.get_integrations_and_groups_from_paths(dst)
    )
    identifiers: set[str] = set()
    duplicates: list[tuple[str, str]] = []
    def_files: list[BuiltFullDetailsIntegrationMetadata] = []
    for i in products.integrations:
        mjd: MarketplaceJsonDefinition = MarketplaceJsonDefinition(i)
        def_file_path: pathlib.Path = i / mp.core.constants.INTEGRATION_DEF_FILE.format(
            i.name,
        )
        def_file: BuiltFullDetailsIntegrationMetadata = mjd.get_def_file(def_file_path)

        identifier: str = def_file["Identifier"]
        if identifier in identifiers:
            duplicates.append((identifier, def_file["DisplayName"]))

        identifiers.add(identifier)
        def_files.append(def_file)

    if duplicates:
        names: str = "\n".join(
            f"Identifier: {d[0]}, DisplayName: {d[1]}" for d in duplicates
        )
        msg: str = f"The following integrations have duplicates: {names}"
        raise DuplicateIntegrationIdentifierInMarketplaceError(msg)

    marketplace_json: pathlib.Path = dst / mp.core.constants.MARKETPLACE_JSON_NAME
    marketplace_json.write_text(
        json.dumps(def_files, sort_keys=True, indent=4),
        encoding="UTF-8",
    )


@dataclasses.dataclass(slots=True, frozen=True)
class MarketplaceJsonDefinition:
    integration_path: pathlib.Path

    def get_def_file(
        self,
        def_file_path: pathlib.Path,
    ) -> BuiltFullDetailsIntegrationMetadata:
        """Get an integration's marketplace JSON definition.

        Args:
            def_file_path: The integration's `.def` file's path

        Returns:
            An integrations built version of the marketplace JSON definition

        """
        metadata: BuiltFullDetailsIntegrationMetadata = json.loads(
            def_file_path.read_text(encoding="utf-8"),
        )
        attrs: FullDetailsExtraAttrs = self._get_full_details_attrs(metadata)
        metadata.update(attrs)
        return mp.core.utils.copy_mapping_without_none_values(metadata)  # type: ignore[return-value]

    def _get_full_details_attrs(
        self,
        integration_metadata: BuiltFullDetailsIntegrationMetadata,
    ) -> FullDetailsExtraAttrs:
        release_times: ReleaseTimes = self._get_integration_release_time(
            integration_metadata,
        )
        return mp.core.utils.copy_mapping_without_none_values(  # type: ignore[return-value]
            {
                "HasConnectors": self._has_connectors(),
                "SupportedActions": self._get_supported_actions(),
                "LatestReleasePublishTimeUnixTime": release_times.latest_release,
                "UpdateNotificationExpired": release_times.update_notification,
                "NewNotificationExpired": release_times.new_notification,
            },
        )

    def _get_integration_release_time(
        self,
        def_file: BuiltFullDetailsIntegrationMetadata,
    ) -> ReleaseTimes:
        release_notes: Sequence[ReleaseNote] = ReleaseNote.from_built_integration_path(
            self.integration_path,
        )
        latest_release_time: int | None = _calculate_latest_release_time(release_notes)
        if latest_release_time is None or latest_release_time < 0:
            return ReleaseTimes(None, None, None)

        return ReleaseTimes(
            latest_release=latest_release_time,
            update_notification=_get_update_notification_time(latest_release_time),
            new_notification=(
                _get_new_notification_time(latest_release_time)
                if int(def_file["Version"]) == 1
                else None
            ),
        )

    def _has_connectors(self) -> bool:
        return any(ConnectorMetadata.from_built_integration_path(self.integration_path))

    def _get_supported_actions(self) -> list[BuiltSupportedAction]:
        actions_definitions: pathlib.Path = (
            self.integration_path / mp.core.constants.OUT_ACTIONS_META_DIR
        )
        if not actions_definitions.exists():
            return []

        supported_action: list[BuiltSupportedAction] = []
        for action_meta_path in actions_definitions.iterdir():
            action_meta: BuiltActionMetadata = json.loads(
                action_meta_path.read_text(encoding="utf-8"),
            )
            supported_action.append(
                {
                    "Name": action_meta["Name"],
                    "Description": action_meta["Description"],
                },
            )

        return supported_action


def _calculate_latest_release_time(release_notes: Iterable[ReleaseNote]) -> int | None:
    if not release_notes:
        return 0

    latest_version: float = max(rn.version for rn in release_notes)
    latest_version_rn: list[ReleaseNote] = [
        rn for rn in release_notes if rn.version == latest_version
    ]
    if not latest_version:
        return None

    return latest_version_rn[0].publish_time


def _get_update_notification_time(latest_release_time: int) -> int:
    return UPDATE_NOTIFICATIONS_DAYS * DAY_IN_MILLISECONDS + latest_release_time


def _get_new_notification_time(latest_release_time: int) -> int:
    return NEW_NOTIFICATION_DAYS * DAY_IN_MILLISECONDS + latest_release_time
