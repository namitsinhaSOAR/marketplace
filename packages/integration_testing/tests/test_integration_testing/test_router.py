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

from typing import TYPE_CHECKING

from integration_testing import router
from integration_testing.request import HttpMethod

if TYPE_CHECKING:
    from integration_testing.requests.session import UrlPath


def test_add_routes() -> None:
    url1 = "/route/one"
    url2 = "/route/two"
    url3 = "/route/three"
    routes: dict[HttpMethod, list[UrlPath]] = {
        HttpMethod.GET: [url1, url2],
        HttpMethod.POST: [url3],
    }

    @router.add_routes(routes)
    def some_func() -> None:
        return

    assert url1 in some_func.__routes__[HttpMethod.GET.value]
    assert url2 in some_func.__routes__[HttpMethod.GET.value]
    assert url3 in some_func.__routes__[HttpMethod.POST.value]


def test_get() -> None:
    url: UrlPath = "/route/one"

    @router.get(url)
    def some_func() -> None:
        return

    assert url in some_func.__routes__[HttpMethod.GET.value]


def test_delete() -> None:
    url: UrlPath = "/route/one"

    @router.delete(url)
    def some_func() -> None:
        return

    assert url in some_func.__routes__[HttpMethod.DELETE.value]


def test_post() -> None:
    url: UrlPath = "/route/one"

    @router.post(url)
    def some_func() -> None:
        return

    assert url in some_func.__routes__[HttpMethod.POST.value]


def test_put() -> None:
    url: UrlPath = "/route/one"

    @router.put(url)
    def some_func() -> None:
        return

    assert url in some_func.__routes__[HttpMethod.PUT.value]


def test_patch() -> None:
    url: UrlPath = "/route/one"

    @router.patch(url)
    def some_func() -> None:
        return

    assert url in some_func.__routes__[HttpMethod.PATCH.value]


def test_multiple_decorators() -> None:
    url1: UrlPath = "/route/one"
    url2: UrlPath = "/route/two"
    url3: UrlPath = "/route/two"

    @router.get(url1)
    @router.get(url2)
    @router.post(url2)
    @router.patch(url3)
    def some_func() -> None:
        return

    assert url1 in some_func.__routes__[HttpMethod.GET.value]
    assert url2 in some_func.__routes__[HttpMethod.GET.value]
    assert url2 in some_func.__routes__[HttpMethod.POST.value]
    assert url3 in some_func.__routes__[HttpMethod.PATCH.value]
