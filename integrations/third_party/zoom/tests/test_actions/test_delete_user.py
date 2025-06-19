from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from ...actions import DeleteUser
from ..common import CONFIG_PATH
from ..core.product import Zoom
from ..core.session import ZoomSession


class TestDeleteUser:
    USER_EMAIL = "user.to.delete@example.com"
    TRANSFER_EMAIL = "admin@example.com"
    TRANSFER_RECORDING = "true"
    TRANSFER_WEBINAR = "false"
    TRANSFER_MEETING = "true"

    @set_metadata(
        parameters={
            "Deleted User Email": USER_EMAIL,
            "Transfer Email": TRANSFER_EMAIL,
            "Transfer Recordings": TRANSFER_RECORDING,
            "Transfer Webinar": TRANSFER_WEBINAR,
            "Transfer Meeting": TRANSFER_MEETING,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_delete_user_success(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        # Set up responses for the transfer checks
        zoom.set_list_meetings_response({"total_records": 1})
        zoom.set_delete_user_response(b"")

        DeleteUser.main()

        # Assert that the correct API calls were made
        delete_user_request = None
        for req_response in script_session.request_history:
            if "/Users/" in req_response.request.url.path and req_response.request.method == "DELETE":
                delete_user_request = req_response.request
                break

        assert delete_user_request is not None
        assert self.USER_EMAIL in delete_user_request.url.path
        
        # Verify query parameters are in the URL
        url_path = delete_user_request.url.path
        assert f"transfer_email={self.TRANSFER_EMAIL}" in url_path
        assert f"transfer_recording={self.TRANSFER_RECORDING}" in url_path
        assert f"transfer_meeting={self.TRANSFER_MEETING}" in url_path
        assert f"transfer_webinar={self.TRANSFER_WEBINAR}" in url_path

        assert action_output.results.output_message == "The account was deleted successfully"
        assert action_output.results.execution_state == ExecutionState.COMPLETED
        
        # Check JSON result
        json_result = action_output.results.json_output.json_result
        assert "isDeleted" in json_result
        assert json_result["isDeleted"] is True

    @set_metadata(
        parameters={
            "Deleted User Email": USER_EMAIL,
            "Transfer Email": TRANSFER_EMAIL,
            "Transfer Recordings": TRANSFER_RECORDING,
            "Transfer Webinar": TRANSFER_WEBINAR,
            "Transfer Meeting": TRANSFER_MEETING,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_delete_user_failure(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        with zoom.fail_requests():
            DeleteUser.main()

        # Assert that API calls were attempted
        assert len(script_session.request_history) >= 1

        assert "Unknown error" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.FAILED
        
        # Check JSON result
        json_result = action_output.results.json_output.json_result
        assert "isDeleted" in json_result
        assert json_result["isDeleted"] is False