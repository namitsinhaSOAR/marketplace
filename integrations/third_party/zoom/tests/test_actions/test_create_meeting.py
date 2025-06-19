from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from ...actions import CreateMeeting
from ..common import CONFIG_PATH
from ..core.product import Zoom
from ..core.session import ZoomSession


class TestCreateMeeting:
    MEETING_TOPIC = "Test Meeting"
    MEETING_TYPE = "Scheduled"
    MEETING_START_TIME = "2024-01-01 10:00:00"
    MEETING_DURATION = "60"
    TIME_ZONE = "UTC"
    AUTO_RECORDING_TYPE = "cloud"
    HOST_EMAIL = "test@example.com"

    @set_metadata(
        parameters={
            "Meeting Topic": MEETING_TOPIC,
            "Meeting Type": MEETING_TYPE,
            "Meeting Start Time": MEETING_START_TIME,
            "Meeting Duration": MEETING_DURATION,
            "Time Zone": TIME_ZONE,
            "Auto Recording Type": AUTO_RECORDING_TYPE,
            "Host Email Address": HOST_EMAIL,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_create_meeting_success(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        expected_meeting_response = {
            "uuid": "test_meeting_uuid",
            "id": 123456789,
            "host_id": "test_host_id",
            "topic": self.MEETING_TOPIC,
            "type": 2,
            "status": "waiting",
            "start_time": self.MEETING_START_TIME,
            "duration": int(self.MEETING_DURATION),
            "timezone": self.TIME_ZONE,
            "join_url": "https://zoom.us/j/123456789",
            "password": "test_password",
            "settings": {
                "auto_recording": self.AUTO_RECORDING_TYPE
            }
        }

        zoom.set_create_meeting_response(expected_meeting_response)

        CreateMeeting.main()

        # Assert that the correct API calls were made
        create_meeting_request = None
        for req_response in script_session.request_history:
            if "/meetings" in req_response.request.url.path and req_response.request.method == "POST":
                create_meeting_request = req_response.request
                break

        assert create_meeting_request is not None
        assert self.HOST_EMAIL in create_meeting_request.url.path

        assert action_output.results.output_message == "The meeting was created successfully"
        assert action_output.results.execution_state == ExecutionState.COMPLETED
        assert action_output.results.json_output.json_result == expected_meeting_response

    @set_metadata(
        parameters={
            "Meeting Topic": MEETING_TOPIC,
            "Meeting Type": MEETING_TYPE,
            "Meeting Start Time": MEETING_START_TIME,
            "Meeting Duration": MEETING_DURATION,
            "Time Zone": TIME_ZONE,
            "Auto Recording Type": AUTO_RECORDING_TYPE,
            "Host Email Address": HOST_EMAIL,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_create_meeting_failure(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        with zoom.fail_requests():
            CreateMeeting.main()

        # Assert that API calls were attempted
        assert len(script_session.request_history) >= 1

        assert "Error trying to create a meeting" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.FAILED