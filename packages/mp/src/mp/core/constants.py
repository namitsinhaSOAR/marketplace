"""Core constants that can be used across multiple apps/components."""

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

PROJECT_FILE: str = "pyproject.toml"
INTEGRATIONS_DIR_NAME: str = "integrations"
COMMUNITY_DIR_NAME: str = "third_party"
COMMERCIAL_DIR_NAME: str = "commercial"
OUT_INTEGRATIONS_DIR_NAME: str = "integrations"
OUT_DIR_NAME: str = "out"
REQUIREMENTS_FILE: str = "requirements.txt"
INTEGRATION_DEF_FILE: str = "Integration-{0}.def"
INTEGRATION_FULLDETAILS_FILE: str = "{0}.fulldetails"
RN_JSON_FILE: str = "RN.json"
OUT_DEPENDENCIES_DIR: str = "Dependencies"
INTEGRATION_VENV: str = ".venv"
MARKETPLACE_JSON_NAME: str = "marketplace.json"

OUT_ACTIONS_META_DIR: str = "ActionsDefinitions"
OUT_CONNECTORS_META_DIR: str = "Connectors"
OUT_JOBS_META_DIR: str = "Jobs"
OUT_WIDGETS_META_DIR: str = "Widgets"

ACTIONS_META_SUFFIX: str = ".actiondef"
CONNECTORS_META_SUFFIX: str = ".connectordef"
JOBS_META_SUFFIX: str = ".jobdef"
WIDGETS_META_SUFFIX: str = ".json"
DEF_FILE_SUFFIX: str = ".yaml"

OUT_ACTION_SCRIPTS_DIR: str = "ActionsScripts"
OUT_CONNECTOR_SCRIPTS_DIR: str = "ConnectorsScripts"
OUT_JOB_SCRIPTS_DIR: str = "JobsScrips"
OUT_WIDGET_SCRIPTS_DIR: str = "WidgetsScripts"
OUT_MANAGERS_SCRIPTS_DIR: str = "Managers"
OUT_TESTS_SCRIPTS_DIR: str = "Tests"
OUT_CUSTOM_FAMILIES_DIR: str = "DefaultCustomFamilies"
OUT_CUSTOM_FAMILIES_FILE: str = "integration_families.json"
OUT_MAPPING_RULES_DIR: str = "DefaultMappingRules"
OUT_MAPPING_RULES_FILE: str = "integration_mapping_rules.json"

CUSTOM_FAMILIES_FILE: str = f"integration_families{DEF_FILE_SUFFIX}"
MAPPING_RULES_FILE: str = f"integration_mapping_rules{DEF_FILE_SUFFIX}"
ACTIONS_DIR: str = "actions"
CONNECTORS_DIR: str = "connectors"
JOBS_DIR: str = "jobs"
WIDGETS_DIR: str = "widgets"
TESTS_DIR: str = "tests"
CORE_SCRIPTS_DIR: str = "core"
PACKAGE_FILE: str = "__init__.py"
COMMON_SCRIPTS_DIR: str = "group_modules"
DEFINITION_FILE: str = f"definition{DEF_FILE_SUFFIX}"
RELEASE_NOTES_FILE: str = f"release_notes{DEF_FILE_SUFFIX}"
SDK_PACKAGE_NAME: str = "soar_sdk"

README_FILE: str = "README.md"
LOCK_FILE: str = "uv.lock"
PYTHON_VERSION_FILE: str = ".python-version"

MS_IN_SEC: int = 1_000
MINIMUM_SYSTEM_VERSION: float = 5.3
ALLOWED_PYTHON_VERSIONS: set[str] = {"3.11", "3.12"}
