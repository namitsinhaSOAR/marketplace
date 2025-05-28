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

import dataclasses
import enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import urllib.parse


class HttpMethod(enum.Enum):
    GET = "GET"
    DELETE = "DELETE"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"


@dataclasses.dataclass(slots=True, frozen=True)
class MockRequest:
    method: HttpMethod
    url: urllib.parse.ParseResult
    headers: dict[str, str]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    @property
    def real_url(self) -> str:
        """Get the 'real' human URL path."""
        return self.url.path
