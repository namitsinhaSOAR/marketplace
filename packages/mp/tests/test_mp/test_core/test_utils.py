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

import pytest

import mp.core.utils


@pytest.mark.parametrize(
    ("input_string", "expected_output"),
    [
        ("CamelCase", "camel_case"),
        ("snake_case", "snake_case"),
        ("camelCase123", "camel_case123"),
        ("Camel-Case", "camel_case"),
        ("Space Case", "space_case"),
        ("123Number", "123_number"),
        ("ALLCAPS", "allcaps"),
        ("alllower", "alllower"),
    ],
)
def test_str_to_snake_case(input_string: str, expected_output: str) -> None:
    assert mp.core.utils.str_to_snake_case(input_string) == expected_output


@pytest.mark.parametrize(
    ("input_string", "expected_output"),
    [
        (">=3.11", "3.11"),
        ("==3.7", "3.7"),
        ("~=3.12", "3.12"),
        ("!=3.13", "3.13"),
        ("<=2.7", "2.7"),
        ("<3.7", "3.7"),
        (">3.14", "3.14"),
        ("===1.0", "1.0"),
        ("==>2.0", "2.0"),
        ("==<3.0", "3.0"),
        ("!==4.0", "4.0"),
        (">=3.11,<3.13", "3.11"),
        ("<3.13,>=3.11", "3.11"),
        (">=3.11, <3.13", "3.11"),
        ("<3.13, >=3.11", "3.11"),
        ("==3.7, <3.13", "3.7"),
        (">3.7, <2.7", "2.7"),
    ],
)
def test_get_python_version_from_string(
    input_string: str,
    expected_output: str,
) -> None:
    assert (
        mp.core.utils.get_python_version_from_version_string(input_string)
        == expected_output
    )
