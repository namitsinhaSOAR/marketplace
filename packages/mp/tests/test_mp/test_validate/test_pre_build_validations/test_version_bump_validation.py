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

import pathlib
import shutil
import tempfile
import unittest.mock

import pytest

import mp.core.unix
from mp.core.exceptions import NonFatalValidationError
from mp.validate.pre_build_validation.version_bump_validation import (
    _create_data_for_version_bump_validation,  # noqa: PLC2701
    _version_bump_validation_run_checks,  # noqa: PLC2701
)


@pytest.fixture
def temp_integration() -> pathlib.Path:
    """Create a temporary integration directory with mock files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)

        test_file_dir = pathlib.Path(__file__).parent
        mock_path = (
            test_file_dir / ".." / ".." / "mock_marketplace" / "third_party" / "mock_integration"
        )
        mock_path = mock_path.resolve()
        shutil.copytree(mock_path, temp_path / "mock_integration")

        yield temp_path / "mock_integration"


class TestVersionBumpValidationFlow:
    def test_valid_existing_integration_version_bump_flow(
        self, temp_integration: pathlib.Path
    ) -> None:
        """Test complete flow for existing integration with valid version bump."""
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        old_toml_content = """[project]
name = "mock_integration"
version = "1.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]"""

        old_rn_content = """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket"""

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "2.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket
-   deprecated: false
    description: Version 2.0 update
    integration_version: 2.0
    item_name: Integration Name
    item_type: Integration
    new: false
    regressive: false
    removed: false
    ticket_number: UPDATE-123""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = lambda path: (
                old_toml_content if path.name == "pyproject.toml" else old_rn_content
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert existing_files["toml"]["old"] is not None
            assert existing_files["toml"]["new"] is not None
            assert existing_files["toml"]["old"].project.version == 1.0
            assert existing_files["toml"]["new"].project.version == 2.0

            try:
                _version_bump_validation_run_checks(existing_files, new_files)
            except NonFatalValidationError:
                pytest.fail("Valid version bump should not raise an exception")

    def test_invalid_existing_integration_version_bump_flow(
        self, temp_integration: pathlib.Path
    ) -> None:
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        old_toml_content = """[project]
name = "mock_integration"
version = "1.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]"""

        old_rn_content = """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket"""

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "3.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket
-   deprecated: false
    description: Version 3.0 update
    integration_version: 3.0
    item_name: Integration Name
    item_type: Integration
    new: false
    regressive: false
    removed: false
    ticket_number: UPDATE-456""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = lambda path: (
                old_toml_content if path.name == "pyproject.toml" else old_rn_content
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert existing_files["toml"]["old"] is not None
            assert existing_files["toml"]["new"] is not None
            assert existing_files["toml"]["old"].project.version == 1.0
            assert existing_files["toml"]["new"].project.version == 3.0

            with pytest.raises(
                NonFatalValidationError, match=r"must be incremented by exactly 1\.0"
            ):
                _version_bump_validation_run_checks(existing_files, new_files)

    def test_mismatched_release_note_version_flow(self, temp_integration: pathlib.Path) -> None:
        """Test complete flow for existing integration with mismatched release note version."""
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        old_toml_content = """[project]
name = "mock_integration"
version = "1.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]"""

        old_rn_content = """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket"""

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "2.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket
-   deprecated: false
    description: Version update
    integration_version: 4.0
    item_name: Integration Name
    item_type: Integration
    new: false
    regressive: false
    removed: false
    ticket_number: UPDATE-789""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = lambda path: (
                old_toml_content if path.name == "pyproject.toml" else old_rn_content
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert existing_files["toml"]["old"] is not None
            assert existing_files["toml"]["new"] is not None
            assert existing_files["toml"]["old"].project.version == 1.0
            assert existing_files["toml"]["new"].project.version == 2.0

            with pytest.raises(NonFatalValidationError, match="release note's version must match"):
                _version_bump_validation_run_checks(existing_files, new_files)

    def test_valid_new_integration_flow(self, temp_integration: pathlib.Path) -> None:
        """Test complete flow for new integration with valid initial version."""
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "1.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: false
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Integration Name
    item_type: Integration
    new: true
    regressive: false
    removed: false
    ticket_number: NEW-123""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = mp.core.unix.NonFatalCommandError(
                "File not found on main branch"
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert not existing_files["toml"].get("old")
            assert not existing_files["toml"].get("new")
            assert new_files["toml"] is not None
            assert new_files["toml"].project.version == 1.0
            assert new_files["rn"] is not None
            assert len(new_files["rn"]) == 1
            assert new_files["rn"][0].version == 1.0

            try:
                _version_bump_validation_run_checks(existing_files, new_files)
            except NonFatalValidationError:
                pytest.fail("Valid new integration should not raise an exception")

    def test_invalid_new_integration_wrong_version_flow(
        self, temp_integration: pathlib.Path
    ) -> None:
        """Test complete flow for new integration with invalid initial version."""
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "2.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: false
    description: New Integration Added - Mock Integration.
    integration_version: 2.0
    item_name: Integration Name
    item_type: Integration
    new: true
    regressive: false
    removed: false
    ticket_number: NEW-456""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = mp.core.unix.NonFatalCommandError(
                "File not found on main branch"
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert not existing_files["toml"].get("old")
            assert not existing_files["toml"].get("new")
            assert new_files["toml"] is not None
            assert new_files["toml"].project.version == 2.0
            assert new_files["rn"] is not None
            assert len(new_files["rn"]) == 1
            assert new_files["rn"][0].version == 2.0

            with pytest.raises(NonFatalValidationError, match=r"must be initialize to 1\.0"):
                _version_bump_validation_run_checks(existing_files, new_files)

    def test_invalid_new_integration_mismatched_rn_version_flow(
        self, temp_integration: pathlib.Path
    ) -> None:
        """Test complete flow for new integration with mismatched release note version."""
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "1.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: false
    description: New Integration Added - Mock Integration.
    integration_version: 2.0
    item_name: Integration Name
    item_type: Integration
    new: true
    regressive: false
    removed: false
    ticket_number: NEW-789""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = mp.core.unix.NonFatalCommandError(
                "File not found on main branch"
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert not existing_files["toml"].get("old")
            assert not existing_files["toml"].get("new")
            assert new_files["toml"] is not None
            assert new_files["toml"].project.version == 1.0
            assert new_files["rn"] is not None
            assert len(new_files["rn"]) == 1
            assert new_files["rn"][0].version == 2.0

            with pytest.raises(NonFatalValidationError, match=r"must be initialize to 1\.0"):
                _version_bump_validation_run_checks(existing_files, new_files)

    def test_integration_with_multiple_new_release_notes_flow(
        self, temp_integration: pathlib.Path
    ) -> None:
        """Test complete flow for existing integration with multiple new release notes."""
        rn_path = temp_integration / "release_notes.yaml"
        toml_path = temp_integration / "pyproject.toml"

        old_toml_content = """[project]
name = "mock_integration"
version = "1.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]"""

        old_rn_content = """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket"""

        toml_path.write_text(
            """[project]
name = "mock_integration"
version = "2.0"
description = "Mock Integration description"
requires-python = ">=3.11"
dependencies = [
    "requests==2.32.4",
]""",
            encoding="utf-8",
        )

        rn_path.write_text(
            """# Copyright header
-   deprecated: true
    description: New Integration Added - Mock Integration.
    integration_version: 1.0
    item_name: Connector Name
    item_type: Connector
    new: true
    regressive: false
    removed: false
    ticket_number: some ticket
-   deprecated: false
    description: Feature A added
    integration_version: 2.0
    item_name: Action A
    item_type: Action
    new: true
    regressive: false
    removed: false
    ticket_number: FEAT-A
-   deprecated: false
    description: Feature B added
    integration_version: 2.0
    item_name: Action B
    item_type: Action
    new: true
    regressive: false
    removed: false
    ticket_number: FEAT-B""",
            encoding="utf-8",
        )

        with unittest.mock.patch("mp.core.unix.get_file_content_from_main_branch") as mock_git:
            mock_git.side_effect = lambda path: (
                old_toml_content if path.name == "pyproject.toml" else old_rn_content
            )

            existing_files, new_files = _create_data_for_version_bump_validation(rn_path, toml_path)

            assert existing_files["toml"]["old"] is not None
            assert existing_files["toml"]["new"] is not None
            assert existing_files["toml"]["old"].project.version == 1.0
            assert existing_files["toml"]["new"].project.version == 2.0

            new_notes = existing_files["rn"]["new"]
            assert new_notes is not None
            assert len(new_notes) == 2  # Two new notes added
            assert all(note.version == 2.0 for note in new_notes)

            try:
                _version_bump_validation_run_checks(existing_files, new_files)
            except NonFatalValidationError:
                pytest.fail(
                    "Valid version bump with multiple release notes should not raise an exception"
                )
