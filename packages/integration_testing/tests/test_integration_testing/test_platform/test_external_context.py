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

import pytest
from TIPCommon.data_models import DatabaseContextType

from integration_testing.platform.external_context import (
    ExternalContextRow,
    ExternalContextRowKey,
    MockExternalContext,
)


class TestInitialization:
    def test_without_parameters(self) -> None:
        ec: MockExternalContext = MockExternalContext()

        assert ec.number_of_rows == 0

    def test_with_parameters(self, ec_row: ExternalContextRow[str]) -> None:
        another_row: ExternalContextRow[str] = ExternalContextRow(
            DatabaseContextType.ALERT,
            "id",
            "key",
            "val",
        )
        rows: list[ExternalContextRow[str]] = [ec_row, another_row]
        ec: MockExternalContext = MockExternalContext(rows)

        assert ec.number_of_rows == len(rows)

    def test_init_rows_are_stored_in_context(
        self,
        ec_row: ExternalContextRow[str],
        ec_row_key: ExternalContextRowKey,
    ) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext(rows)

        row_value: str = ec.get_row_value(
            context_type=ec_row_key.context_type,
            identifier=ec_row_key.identifier,
            property_key=ec_row_key.property_key,
        )

        assert row_value == ec_row.property_value


class TestMethods:
    def test_has_row(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        row_key: ExternalContextRowKey = ExternalContextRowKey(
            ec_row.context_type,
            ec_row.identifier,
            ec_row.property_key,
        )
        ec: MockExternalContext = MockExternalContext(rows)
        another_row: ExternalContextRow[str] = ExternalContextRow(
            DatabaseContextType.ALERT,
            "id",
            "key",
            "val",
        )

        assert ec.has_row(ec_row) is True
        assert ec.has_row(row_key) is True
        assert ec.has_row(another_row) is False
        assert ec_row in ec
        assert another_row not in ec
        assert row_key in ec

    def test_get_row_value(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext(rows)

        assert ec.number_of_rows == len(rows)

        context_row_value: str = ec.get_row_value(
            context_type=ec_row.context_type,
            identifier=ec_row.identifier,
            property_key=ec_row.property_key,
        )

        assert context_row_value == ec_row.property_value

    def test_get_non_existing_row_returns_none(
        self,
        ec_row: ExternalContextRow[str],
    ) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext(rows)

        assert ec.number_of_rows == len(rows)

        context_row_value: str = ec.get_row_value(
            context_type=ec_row.context_type,
            identifier="some id",
            property_key="some key",
        )

        assert context_row_value is None

    def test_set_row_value(self, ec_row: ExternalContextRow[str]) -> None:
        ec: MockExternalContext = MockExternalContext()

        assert ec.number_of_rows == 0

        ec.set_row_value(
            context_type=ec_row.context_type,
            identifier=ec_row.identifier,
            property_key=ec_row.property_key,
            property_value=ec_row.property_value,
        )

        assert ec.number_of_rows == 1

        context_row_value: str = ec.get_row_value(
            context_type=ec_row.context_type,
            identifier=ec_row.identifier,
            property_key=ec_row.property_key,
        )

        assert context_row_value == ec_row.property_value

    def test_override_row_value(self, ec_row: ExternalContextRow[str]) -> None:
        ec: MockExternalContext[str] = MockExternalContext([ec_row])

        assert ec.number_of_rows == 1

        new_value: str = "New Value"
        ec.set_row_value(
            context_type=ec_row.context_type,
            identifier=ec_row.identifier,
            property_key=ec_row.property_key,
            property_value=new_value,
        )

        assert ec.number_of_rows == 1

        context_row_value: str = ec.get_row_value(
            context_type=ec_row.context_type,
            identifier=ec_row.identifier,
            property_key=ec_row.property_key,
        )

        assert context_row_value == new_value

    def test_delete_existing_row(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext[str] = MockExternalContext(rows)

        assert ec.number_of_rows == len(rows)

        ec.delete_row(
            context_type=ec_row.context_type,
            identifier=ec_row.identifier,
            property_key=ec_row.property_key,
        )

        assert ec.number_of_rows == 0

    def test_delete_non_existing_row_raise_value_error(
        self,
        ec_row: ExternalContextRow[str],
    ) -> None:
        ec: MockExternalContext = MockExternalContext()

        with pytest.raises(ValueError, match="Could not find a value in the external"):
            ec.delete_row(
                context_type=ec_row.context_type,
                identifier="some id",
                property_key="some key",
            )

    def test_set_rows(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext()

        assert ec.number_of_rows == 0

        ec.set_rows(rows)

        assert ec.number_of_rows == len(rows)

    def test_override_rows(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext(rows)

        assert ec.number_of_rows == len(rows)

        ec.set_rows(rows)

        assert ec.number_of_rows == len(rows)

    def test_delete_non_existing_rows(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext()

        with pytest.raises(ValueError, match="Could not find a value in the external"):
            ec.delete_rows(rows)

    def test_delete_non_existing_and_existing_rows_still_deletes_existing_rows(
        self,
        ec_row: ExternalContextRow[str],
    ) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext(rows)
        non_existing_row: ExternalContextRow[str] = ExternalContextRow(
            ec_row.context_type,
            "id2",
            "key2",
            "val2",
        )
        assert ec.number_of_rows == 1

        with pytest.raises(ValueError, match="Could not find a value in the external"):
            ec.delete_rows([ec_row, non_existing_row])

        assert ec.number_of_rows == 0

    def test_drop(self, ec_row: ExternalContextRow[str]) -> None:
        rows: list[ExternalContextRow[str]] = [ec_row]
        ec: MockExternalContext = MockExternalContext(rows)

        assert ec.number_of_rows == len(rows)

        ec.drop()

        assert ec.number_of_rows == 0
