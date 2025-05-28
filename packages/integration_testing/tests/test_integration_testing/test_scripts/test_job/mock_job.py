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

from TIPCommon.base.job import Job

if TYPE_CHECKING:
    from TIPCommon.data_models import Container, DatabaseContextType
    from TIPCommon.types import SingleJson


class MockJob(Job[None]):
    def __init__(self) -> None:
        super().__init__("Mock Job")

    def _validate_params(self) -> None:
        pass

    def _perform_job(self) -> None:
        pass

    def _init_api_clients(self) -> None:
        return

    def set_parameters(self) -> Container:
        self._extract_job_params()
        return self.params

    def set_external_context(
        self,
        context_type: DatabaseContextType,
        identifier: str,
        key: str,
        value: str,
    ) -> None:
        """Set context property to external context."""
        self.soar_job.set_context_property(
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
        return self.soar_job.get_context_property(
            context_type=context_type,
            identifier=identifier,
            property_key=key,
        )

    def get_input_context(self) -> SingleJson:
        return {
            "parameters": self.soar_job.parameters,
            "unique_identifier": self.soar_job.unique_identifier,
            "use_proxy_settings": self.soar_job.use_proxy_settings,
            "vault_settings": self.soar_job.vault_settings,
            "job_api_key": self.soar_job.job_api_key,
        }

    def get_integration_configuration(self) -> SingleJson:
        return self.soar_job.get_configuration(self.name)

    def get_job_parameters(self) -> SingleJson:
        return self.soar_job.parameters
