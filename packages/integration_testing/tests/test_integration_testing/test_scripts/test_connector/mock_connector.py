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

import copy
from typing import TYPE_CHECKING, Any

from soar_sdk.SiemplifyConnectorsDataModel import AlertInfo, ConnectorContext
from TIPCommon.base.connector import Connector
from TIPCommon.data_models import BaseAlert, DatabaseContextType

if TYPE_CHECKING:
    from TIPCommon.types import SingleJson


class MockConnector(Connector):
    def __init__(self) -> None:
        super().__init__("Mock Connector")
        self.alert_to_ingest: AlertInfo | None = None

    def get_connector_parameters(self) -> SingleJson:
        return self.siemplify.parameters

    def validate_params(self) -> None:
        pass

    def init_managers(self) -> None:
        pass

    def get_alerts(self) -> list[BaseAlert]:
        return [BaseAlert(alert_id="", raw_data={})]

    def create_alert_info(self, _: Any) -> AlertInfo:  # noqa: ANN401
        """Create mock alert info."""
        if self.alert_to_ingest is not None:
            return self.alert_to_ingest

        alert: AlertInfo = AlertInfo()
        alert.environment = "environment"
        alert.device_product = "product"
        alert.rule_generator = "rule"
        return alert

    def set_alert_to_ingest(self, alert: AlertInfo) -> None:
        self.alert_to_ingest = copy.deepcopy(alert)

    def set_external_context(
        self,
        context_type: DatabaseContextType,
        identifier: str,
        key: str,
        value: str,
    ) -> None:
        """Set context property to external context."""
        self.siemplify.set_context_property(
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
        return self.siemplify.get_context_property(
            context_type=context_type,
            identifier=identifier,
            property_key=key,
        )

    def get_input_context(self) -> ConnectorContext:
        return self.siemplify.context
