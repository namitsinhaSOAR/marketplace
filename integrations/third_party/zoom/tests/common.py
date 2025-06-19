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

import json
import pathlib

INTEGRATION_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent
CONFIG_PATH = pathlib.Path.joinpath(INTEGRATION_PATH, "tests", "config.json")

TEST_CONFIG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
TEST_ACCOUNT_ID = TEST_CONFIG.get("Account ID", "test_account_id")
TEST_CLIENT_ID = TEST_CONFIG.get("Client ID", "test_client_id") 
TEST_CLIENT_SECRET = TEST_CONFIG.get("Client Secret", "test_client_secret")
