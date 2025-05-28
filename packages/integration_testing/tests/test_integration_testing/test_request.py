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

from integration_testing import request as r


def test_initialize_with_parameters() -> None:
    request: r.MockRequest = r.MockRequest(
        method=r.HttpMethod.GET,
        url=urllib.parse.urlparse("/test/url/"),
        headers={},
        args=(),
        kwargs={},
    )

    assert request is not None
