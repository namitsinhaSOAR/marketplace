from __future__ import annotations

import contextlib
import dataclasses

from TIPCommon.types import SingleJson


@dataclasses.dataclass(slots=True)
class Zoom:
    _test_connectivity_response: SingleJson | None = None
    _create_meeting_response: SingleJson | None = None
    _create_user_response: SingleJson | None = None
    _delete_user_response: SingleJson | None = None
    _get_meeting_recording_response: SingleJson | None = None
    _get_user_details_response: SingleJson | None = None
    _list_meetings_response: SingleJson | None = None
    _oauth_token_response: SingleJson | None = None
    _fail_requests_active: bool = False

    @contextlib.contextmanager
    def fail_requests(self):
        self._fail_requests_active = True
        try:
            yield
        finally:
            self._fail_requests_active = False

    def set_test_connectivity_response(self, response: SingleJson):
        self._test_connectivity_response = response

    def set_create_meeting_response(self, response: SingleJson):
        self._create_meeting_response = response

    def set_create_user_response(self, response: SingleJson):
        self._create_user_response = response

    def set_delete_user_response(self, response: SingleJson):
        self._delete_user_response = response

    def set_get_meeting_recording_response(self, response: SingleJson):
        self._get_meeting_recording_response = response

    def set_get_user_details_response(self, response: SingleJson):
        self._get_user_details_response = response

    def set_list_meetings_response(self, response: SingleJson):
        self._list_meetings_response = response

    def set_oauth_token_response(self, response: SingleJson):
        self._oauth_token_response = response

    def oauth_token(self, account_id: str, client_id: str, client_secret: str) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for OAuth token")

        if self._oauth_token_response:
            return self._oauth_token_response

        # Default successful OAuth response
        return {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "meeting:write user:write user:read meeting:read"
        }

    def test_connectivity(self) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for test connectivity")

        if self._test_connectivity_response:
            return self._test_connectivity_response

        # Default successful connectivity response  
        return {
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
        }

    def create_meeting(
        self,
        meeting_topic: str,
        meeting_type: str, 
        meeting_start_time: str,
        meeting_duration: str,
        timezone: str,
        auto_record_meeting_type: str,
        host_email: str
    ) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for create meeting")

        if self._create_meeting_response:
            return self._create_meeting_response

        # Default successful meeting creation response
        return {
            "uuid": "test_meeting_uuid",
            "id": 123456789,
            "host_id": "test_host_id",
            "topic": meeting_topic,
            "type": 2 if meeting_type == "Scheduled" else 1,
            "status": "waiting",
            "start_time": meeting_start_time,
            "duration": int(meeting_duration),
            "timezone": timezone,
            "join_url": "https://zoom.us/j/123456789",
            "password": "test_password",
            "settings": {
                "auto_recording": auto_record_meeting_type
            }
        }

    def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        user_type: str
    ) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for create user")

        if self._create_user_response:
            return self._create_user_response

        # Default successful user creation response
        user_type_mapping = {"Basic": 1, "Licensed": 2, "On-prem": 3}
        return {
            "id": "test_user_id",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "type": user_type_mapping.get(user_type, 1),
            "status": "pending"
        }

    def delete_user(
        self,
        user_email: str,
        transfer_recording: str,
        transfer_webinar: str,
        transfer_meeting: str,
        transfer_email: str
    ) -> bytes:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for delete user")

        if self._delete_user_response:
            return self._delete_user_response

        # Default successful deletion (returns empty content)
        return b""

    def get_meeting_recording(self, meeting_id: str) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for get meeting recording")

        if self._get_meeting_recording_response:
            return self._get_meeting_recording_response

        # Default successful recording response
        return {
            "uuid": f"test_uuid_{meeting_id}",
            "id": int(meeting_id),
            "account_id": "test_account_id",
            "host_id": "test_host_id",
            "topic": "Test Meeting",
            "type": 2,
            "start_time": "2023-01-01T10:00:00Z",
            "duration": 60,
            "total_size": 1234567,
            "recording_count": 1,
            "recording_files": [
                {
                    "id": "test_recording_id",
                    "meeting_id": meeting_id,
                    "recording_start": "2023-01-01T10:00:00Z",
                    "recording_end": "2023-01-01T11:00:00Z",
                    "file_type": "MP4",
                    "file_size": 1234567,
                    "download_url": f"https://example.com/recording/{meeting_id}"
                }
            ]
        }

    def get_user_details(self, user_email: str) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for get user details")

        if self._get_user_details_response:
            return self._get_user_details_response

        # Default successful user details response
        return {
            "id": "test_user_id",
            "first_name": "Test",
            "last_name": "User", 
            "email": user_email,
            "type": 1,
            "status": "active",
            "created_at": "2023-01-01T10:00:00Z",
            "last_login_time": "2023-01-01T10:00:00Z"
        }

    def list_meetings(self, user_email: str) -> SingleJson:
        if self._fail_requests_active:
            raise Exception("Simulated API failure for list meetings")

        if self._list_meetings_response:
            return self._list_meetings_response

        # Default successful meetings list response
        return {
            "page_count": 1,
            "page_number": 1,
            "page_size": 30,
            "total_records": 1,
            "meetings": [
                {
                    "uuid": "test_meeting_uuid",
                    "id": 123456789,
                    "host_id": "test_host_id",
                    "topic": "Test Meeting",
                    "type": 2,
                    "start_time": "2023-01-01T10:00:00Z",
                    "duration": 60,
                    "timezone": "UTC",
                    "join_url": "https://zoom.us/j/123456789"
                }
            ]
        }