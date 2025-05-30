import json
import pathlib
import shutil
from collections.abc import Generator

import pytest

import mp.core.constants
from mp.build_project.post_build.duplicate_integrations import (
    IntegrationExistsError,
    raise_errors_for_duplicate_integrations,
)


@pytest.fixture
def temp_marketplace_paths(
    tmp_path: pathlib.Path,
) -> Generator[tuple[pathlib.Path, pathlib.Path], None, None]:
    commercial = tmp_path / "commercial"
    community = tmp_path / "community"
    commercial.mkdir()
    community.mkdir()

    # Create marketplace.json files to avoid test failures
    _create_marketplace_json(commercial)
    _create_marketplace_json(community)

    yield commercial, community
    shutil.rmtree(tmp_path)


def _create_marketplace_json(marketplace_path: pathlib.Path) -> None:
    """Create an empty marketplace.json file in the given marketplace path.

    Args:
        marketplace_path: Path to the marketplace directory

    """
    mp_json_path = marketplace_path / mp.core.constants.MARKETPLACE_JSON_NAME
    mp_json_path.write_text(json.dumps([]), encoding="utf-8")


def test_duplicate_integration_same_marketplace(
    temp_marketplace_paths: tuple[pathlib.Path, pathlib.Path],
) -> None:
    commercial, _ = temp_marketplace_paths
    integration_path = commercial / "test_integration"
    integration_path.mkdir(parents=True)

    # Create an ` integration.def ` file with identifier
    _create_integration_def(integration_path, "test-integration")

    # Create a duplicate integration in the same marketplace
    duplicate_path = commercial / "test_integration_copy"
    duplicate_path.mkdir(parents=True)
    _create_integration_def(duplicate_path, "test-integration")  # Same identifier

    # Update marketplace.json with duplicates
    _create_marketplace_json_with_integrations(
        commercial,
        [
            {"Identifier": "test-integration", "DisplayName": "Test Integration"},
            {"Identifier": "test-integration", "DisplayName": "Test Integration Copy"},
        ],
    )

    with pytest.raises(
        IntegrationExistsError,
        match="Found multiple integrations with the same identifier: .*",
    ):
        raise_errors_for_duplicate_integrations(commercial, commercial)


def test_duplicate_integration_across_marketplaces(
    temp_marketplace_paths: tuple[pathlib.Path, pathlib.Path],
) -> None:
    commercial, community = temp_marketplace_paths

    # Create the same integration in both marketplaces
    integration_path = commercial / "test_integration"
    integration_path.mkdir(parents=True)
    _create_integration_def(integration_path, "test-integration")

    community_integration = community / "test_integration"
    community_integration.mkdir(parents=True)
    _create_integration_def(community_integration, "test-integration")

    # Update marketplace.json files with the same identifier in both marketplaces
    _create_marketplace_json_with_integrations(
        commercial,
        [{"Identifier": "test-integration", "DisplayName": "Test Integration"}],
    )
    _create_marketplace_json_with_integrations(
        community,
        [{"Identifier": "test-integration", "DisplayName": "Test Integration"}],
    )

    with pytest.raises(
        IntegrationExistsError,
        match="The following integrations found in more than one marketplace:",
    ):
        raise_errors_for_duplicate_integrations(commercial, community)


def _create_integration_def(integration_path: pathlib.Path, identifier: str) -> None:
    """Create an integration definition file with the given identifier.

    Args:
        integration_path: Path to the integration directory
        identifier: The integration identifier to use

    """
    def_file_path = integration_path / mp.core.constants.INTEGRATION_DEF_FILE.format(
        integration_path.name
    )
    def_file_content = {
        "Identifier": identifier,
        "DisplayName": f"{integration_path.name} Integration",
        "Version": "1",
    }
    def_file_path.write_text(json.dumps(def_file_content), encoding="utf-8")


def _create_marketplace_json_with_integrations(
    marketplace_path: pathlib.Path,
    integrations: list[dict],
) -> None:
    """Create a marketplace.json file with the given integrations.

    Args:
        marketplace_path: Path to the marketplace directory
        integrations: List of integration dictionaries to include

    """
    mp_json_path = marketplace_path / mp.core.constants.MARKETPLACE_JSON_NAME
    mp_json_path.write_text(json.dumps(integrations), encoding="utf-8")
