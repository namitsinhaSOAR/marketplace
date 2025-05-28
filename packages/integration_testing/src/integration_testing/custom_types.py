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

import abc
import re
from typing import TYPE_CHECKING, Generic, TypeVar

from .request import MockRequest

if TYPE_CHECKING:
    from collections.abc import MutableMapping

NO_RESPONSE: object = object()

Response = TypeVar("Response")
Request = TypeVar("Request", bound=MockRequest)
Product = TypeVar("Product")

UrlPath = str | re.Pattern


class ActOnRequestFn(abc.ABC, Generic[Response]):
    __routes__: MutableMapping[str, list[UrlPath]]

    @abc.abstractmethod
    def __call__(self, request: Request) -> Response:
        """Type hint for the ActOnRequestFn protocol.

        Args:
            request: the API request

        Returns:
            The API response

        """
