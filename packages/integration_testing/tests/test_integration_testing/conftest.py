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

import urllib.parse
from typing import TYPE_CHECKING

import pytest
from TIPCommon.data_models import DatabaseContextType

from integration_testing.platform.external_context import (
    ExternalContextRow,
    ExternalContextRowKey,
)
from integration_testing.platform.script_output import (
    MockActionOutput,
    MockConnectorOutput,
)
from integration_testing.requests.session import MockSession

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def session() -> Iterator[MockSession]:
    yield MockSession()  # noqa: PT022


@pytest.fixture
def url() -> Iterator[str]:
    yield "https://www.google.com/api/test/path"  # noqa: PT022


@pytest.fixture
def parsed_url(url: str) -> Iterator[urllib.parse.ParseResult]:
    yield urllib.parse.urlparse(url)  # noqa: PT022


@pytest.fixture
def action_output() -> Iterator[MockActionOutput]:
    yield MockActionOutput()  # noqa: PT022


@pytest.fixture
def connector_output() -> Iterator[MockConnectorOutput]:
    yield MockConnectorOutput()  # noqa: PT022


@pytest.fixture
def ec_row() -> Iterator[ExternalContextRow[str]]:
    yield ExternalContextRow(DatabaseContextType.GLOBAL, "identifier", "key", "Value")  # noqa: PT022


@pytest.fixture
def ec_row_key() -> Iterator[ExternalContextRowKey]:
    yield ExternalContextRowKey(DatabaseContextType.GLOBAL, "identifier", "key")  # noqa: PT022
