from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from ...actions import Ping
from ..common import CONFIG_PATH
from ..core.product import Zoom
from ..core.session import ZoomSession


class TestPing:
    @set_metadata(integration_config_file_path=CONFIG_PATH)
    def test_ping_success(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        zoom.set_test_connectivity_response({
            "page_count": 1,
            "page_number": 1,
            "page_size": 30,
            "total_records": 1,
            "users": [
                {
                    "id": "test_user_id",
                    "email": "test@example.com",
                    "type": 1,
                    "status": "active"
                }
            ]
        })

        Ping.main()

        # Assert that the correct API calls were made
        assert len(script_session.request_history) >= 1
        
        # Check for OAuth token request
        oauth_request = None
        connectivity_request = None
        
        for req_response in script_session.request_history:
            if "/oauth/token" in req_response.request.url.path:
                oauth_request = req_response.request
            elif "/v2/users" in req_response.request.url.path:
                connectivity_request = req_response.request
        
        # OAuth request should be made for authentication
        assert oauth_request is not None
        
        # Connectivity test request should be made
        assert connectivity_request is not None
        assert connectivity_request.url.path.endswith("/v2/users")

        assert action_output.results.output_message == "Connected successfully"
        assert action_output.results.execution_state == ExecutionState.COMPLETED

    @set_metadata(integration_config_file_path=CONFIG_PATH)
    def test_ping_failure(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        with zoom.fail_requests():
            Ping.main()

        # Assert that API calls were attempted
        assert len(script_session.request_history) >= 1

        assert "Couldn't connect" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.FAILED