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

from integration_testing.requests import response as r


def test_initialize_with_no_parameters() -> None:
    response: r.MockResponse = r.MockResponse()

    assert response is not None


def test_initialize_with_no_parameters_default_attributes() -> None:
    response: r.MockResponse = r.MockResponse()

    assert not response.content
    assert response.status_code
    assert not response.headers
    assert not response.request
    assert response.raw is not None


def test_initialize_with_json_content_transform_to_string() -> None:
    rc: dict[str, str] = {"Hello": "World"}
    str_rc: str = json.dumps(rc)

    response: r.MockResponse = r.MockResponse(rc)

    assert response.text == str_rc
    assert response.content.decode() == str_rc
