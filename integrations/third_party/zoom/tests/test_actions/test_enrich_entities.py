from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from ...actions import EnrichEntities
from ..common import CONFIG_PATH
from ..core.product import Zoom
from ..core.session import ZoomSession


class TestEnrichEntities:
    USER_EMAIL = "user@example.com"

    @set_metadata(
        entities=[USER_EMAIL],
        integration_config_file_path=CONFIG_PATH,
    )
    def test_enrich_entities_success(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        expected_user_response = {
            "id": "test_user_id",
            "first_name": "Test",
            "last_name": "User",
            "email": self.USER_EMAIL,
            "type": 1,
            "status": "active",
            "created_at": "2023-01-01T10:00:00Z",
            "last_login_time": "2023-01-01T10:00:00Z"
        }

        zoom.set_get_user_details_response(expected_user_response)

        EnrichEntities.main()

        # Assert that the correct API calls were made
        user_details_request = None
        
        for req_response in script_session.request_history:
            if "/users/" in req_response.request.url.path and "/meetings" not in req_response.request.url.path:
                user_details_request = req_response.request
                break

        assert user_details_request is not None
        assert self.USER_EMAIL in user_details_request.url.path

        assert f"The following entities were enriched:\n{self.USER_EMAIL}" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.COMPLETED
        assert action_output.results.result_value == "True"

    @set_metadata(
        entities=[USER_EMAIL],
        integration_config_file_path=CONFIG_PATH,
    )
    def test_enrich_entities_failure(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        with zoom.fail_requests():
            EnrichEntities.main()

        # Assert that API calls were attempted
        assert len(script_session.request_history) >= 1

        assert "No entities were enriched" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.FAILED
        assert action_output.results.result_value == "False"