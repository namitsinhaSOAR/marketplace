from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from ...actions import GetMeetingRecording
from ..common import CONFIG_PATH
from ..core.product import Zoom
from ..core.session import ZoomSession


class TestGetMeetingRecording:
    MEETING_ID = "123456789"

    @set_metadata(
        parameters={
            "Meeting ID": MEETING_ID,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_get_meeting_recording_success(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        expected_recording_response = {
            "uuid": f"test_uuid_{self.MEETING_ID}",
            "id": int(self.MEETING_ID),
            "account_id": "test_account_id",
            "host_id": "test_host_id",
            "topic": "Test Meeting",
            "type": 2,
            "start_time": "2023-01-01T10:00:00Z",
            "duration": 60,
            "total_size": 1234567,
            "recording_count": 1,
            "share_url": f"https://example.com/recording/{self.MEETING_ID}",
            "recording_files": [
                {
                    "id": "test_recording_id",
                    "meeting_id": self.MEETING_ID,
                    "recording_start": "2023-01-01T10:00:00Z",
                    "recording_end": "2023-01-01T11:00:00Z",
                    "file_type": "MP4",
                    "file_size": 1234567,
                    "download_url": f"https://example.com/recording/{self.MEETING_ID}"
                }
            ]
        }

        zoom.set_get_meeting_recording_response(expected_recording_response)

        GetMeetingRecording.main()

        # Assert that the correct API calls were made
        recording_request = None
        for req_response in script_session.request_history:
            if "/meetings/" in req_response.request.url.path and "/recordings" in req_response.request.url.path:
                recording_request = req_response.request
                break

        assert recording_request is not None
        assert self.MEETING_ID in recording_request.url.path

        assert action_output.results.output_message == "The meeting recording was fetched"
        assert action_output.results.execution_state == ExecutionState.COMPLETED
        
        # Check JSON result
        json_result = action_output.results.json_output.json_result
        assert "meetingRecordingDetails" in json_result
        assert json_result["meetingRecordingDetails"] == expected_recording_response

    @set_metadata(
        parameters={
            "Meeting ID": MEETING_ID,
        },
        integration_config_file_path=CONFIG_PATH,
    )
    def test_get_meeting_recording_failure(
        self,
        script_session: ZoomSession,
        action_output: MockActionOutput,
        zoom: Zoom,
    ) -> None:
        with zoom.fail_requests():
            GetMeetingRecording.main()

        # Assert that API calls were attempted
        assert len(script_session.request_history) >= 1

        assert "Couldn't get the meeting recording" in action_output.results.output_message
        assert action_output.results.execution_state == ExecutionState.FAILED