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

from TIPCommon.cache import Cache

from test_integration_testing.test_scripts.test_action.mock_action import MockAction
from test_integration_testing.test_scripts.test_connector.mock_connector import (
    MockConnector,
)
from test_integration_testing.test_scripts.test_job.mock_job import MockJob

from .constants import TEST_CONTEXT_PREFIX


def action_cache(max_size: int | None) -> Cache:
    return Cache(
        chronicle_soar=MockAction(),
        prefix=TEST_CONTEXT_PREFIX,
        max_size=max_size,
    )


def connector_cache(max_size: int | None) -> Cache:
    return Cache(
        chronicle_soar=MockConnector(),
        prefix=TEST_CONTEXT_PREFIX,
        max_size=max_size,
    )


def job_cache(max_size: int | None) -> Cache:
    return Cache(
        chronicle_soar=MockJob(),
        prefix=TEST_CONTEXT_PREFIX,
        max_size=max_size,
    )
