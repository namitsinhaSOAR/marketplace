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

from typing import TYPE_CHECKING, Any

from TIPCommon.base.action import Action

if TYPE_CHECKING:
    from TIPCommon.data_models import DatabaseContextType
    from TIPCommon.types import Entity, SingleJson


class MockAction(Action[None]):
    def __init__(self) -> None:
        super().__init__("Mock Action")

    def _init_api_clients(self) -> None:
        return

    def _perform_action(self, _: Any) -> None:  # noqa: ANN401
        return

    def get_entities(self) -> list[Entity]:
        return self.soar_action.target_entities

    def set_external_context(
        self,
        context_type: DatabaseContextType,
        identifier: str,
        key: str,
        value: str,
    ) -> None:
        """Set context property to external context."""
        self.soar_action.set_context_property(
            context_type=context_type,
            identifier=identifier,
            property_key=key,
            property_value=value,
        )

    def get_external_context(
        self,
        context_type: DatabaseContextType,
        identifier: str,
        key: str,
    ) -> Any:  # noqa: ANN401
        """Get context property from external context."""
        return self.soar_action.get_context_property(
            context_type=context_type,
            identifier=identifier,
            property_key=key,
        )

    def get_input_context(self) -> SingleJson:
        return self.soar_action.context_data

    def get_integration_configuration(self) -> SingleJson:
        return self.soar_action.get_configuration(self.name)

    def get_action_parameters(self) -> SingleJson:
        return self.soar_action.parameters

    def set_output_json(self, output: SingleJson) -> None:
        self.soar_action.result.add_result_json(output)
