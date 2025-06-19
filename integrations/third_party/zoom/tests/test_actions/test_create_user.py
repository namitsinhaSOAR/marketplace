from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from ...actions import CreateUser
from ..common import CONFIG_PATH
from ..core.product import Zoom
from ..core.session import ZoomSession


class TestCreateUser:
    FIRST_NAME = "John"
    LAST_NAME = "Doe"
    EMAIL = "john.doe@example.com"
    USER_TYPE = "Licensed"

    @set_metadata(
        parameters={
            "First Name": FIRST_NAME,
            "Last Name": LAST_NAME,
            "Email": EMAIL,
            "User Type": USER_TYPE,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_create_user_success(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        expected_user_response = {
            "id": "test_user_id",
            "first_name": self.FIRST_NAME,
            "last_name": self.LAST_NAME,
            "email": self.EMAIL,
            "type": 2,  # Licensed user type
            "status": "pending"
        }

        zoom.set_create_user_response(expected_user_response)

        CreateUser.main()

        # Assert that the correct API calls were made
        create_user_request = None
        for req_response in script_session.request_history:
            if req_response.request.url.path.endswith("/v2/users") and req_response.request.method == "POST":
                create_user_request = req_response.request
                break

        assert create_user_request is not None

        assert action_output.results.output_message == "The user was created successfully"
        assert action_output.results.execution_state == ExecutionState.COMPLETED
        
        # Check that the JSON result contains the created user details
        json_result = action_output.results.json_output.json_result
        assert "createdUserDetails" in json_result
        assert json_result["createdUserDetails"] == expected_user_response

    @set_metadata(
        parameters={
            "First Name": FIRST_NAME,
            "Last Name": LAST_NAME,
            "Email": EMAIL,
            "User Type": USER_TYPE,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_create_user_failure(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        with zoom.fail_requests():
            CreateUser.main()

        # Assert that API calls were attempted
        assert len(script_session.request_history) >= 1

        assert "The user wasn't created" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.FAILED