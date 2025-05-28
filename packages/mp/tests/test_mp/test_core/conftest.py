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

import unittest.mock
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_subprocess_run() -> Generator[unittest.mock.MagicMock]:
    with unittest.mock.patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_check_output() -> Generator[unittest.mock.MagicMock]:
    with unittest.mock.patch("subprocess.check_output") as mock_check_output:
        yield mock_check_output
