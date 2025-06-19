from __future__ import annotations

from typing import Any

from .product import Zoom
from integration_testing import router
from integration_testing.common import get_request_payload
from integration_testing.request import MockRequest
from integration_testing.requests.response import MockResponse
from integration_testing.requests.session import MockSession, RouteFunction


class ZoomSession(MockSession[MockRequest, MockResponse, Zoom]):
    def get_routed_functions(self) -> list[RouteFunction]:
        return [
            self.oauth_token,
            self.test_connectivity,
            self.create_meeting,
            self.create_user,
            self.delete_user,
            self.get_meeting_recording,
            self.get_user_details,
            self.list_meetings,
        ]

    @router.post(r"/oauth/token")
    def oauth_token(self, request: MockRequest) -> MockResponse:
        try:
            payload: dict[str, Any] = get_request_payload(request)
            account_id = payload.get("account_id", "")
            
            # Extract auth from basic auth header
            auth = getattr(request, 'auth', ('test_client_id', 'test_client_secret'))
            client_id, client_secret = auth if auth else ('', '')
            
            response_data = self._product.oauth_token(account_id, client_id, client_secret)
            return MockResponse(content=response_data)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.get(r"/v2/users")
    def test_connectivity(self, request: MockRequest) -> MockResponse:
        try:
            response_data = self._product.test_connectivity()
            return MockResponse(content=response_data)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.post(r"/v2/users/[^/]+/meetings")
    def create_meeting(self, request: MockRequest) -> MockResponse:
        try:
            payload: dict[str, Any] = get_request_payload(request)
            
            # Extract host email from URL path
            host_email = request.url.path.split("/users/")[1].split("/meetings")[0]
            
            response_data = self._product.create_meeting(
                meeting_topic=payload.get("topic", ""),
                meeting_type="Scheduled" if payload.get("type") == 2 else "Instant",
                meeting_start_time=payload.get("start_time", ""),
                meeting_duration=str(payload.get("duration", 60)),
                timezone=payload.get("timezone", "UTC"),
                auto_record_meeting_type=payload.get("settings", {}).get("auto_recording", "none"),
                host_email=host_email
            )
            return MockResponse(content=response_data, status_code=201)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.post(r"/v2/users$")
    def create_user(self, request: MockRequest) -> MockResponse:
        try:
            payload: dict[str, Any] = get_request_payload(request)
            user_info = payload.get("user_info", {})
            
            # Map type number back to string
            user_type_mapping = {1: "Basic", 2: "Licensed", 3: "On-prem"}
            user_type = user_type_mapping.get(user_info.get("type", 1), "Basic")
            
            response_data = self._product.create_user(
                first_name=user_info.get("first_name", ""),
                last_name=user_info.get("last_name", ""),
                email=user_info.get("email", ""),
                user_type=user_type
            )
            return MockResponse(content=response_data, status_code=201)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.delete(r"/v2/Users/[^/]+")
    def delete_user(self, request: MockRequest) -> MockResponse:
        try:
            # Extract user email from URL path
            user_email = request.url.path.split("/Users/")[1].split("?")[0]
            
            # Extract query parameters
            query_params = {}
            if "?" in request.url.path:
                query_string = request.url.path.split("?")[1]
                for param in query_string.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        query_params[key] = value
            
            response_data = self._product.delete_user(
                user_email=user_email,
                transfer_recording=query_params.get("transfer_recording", "false"),
                transfer_webinar=query_params.get("transfer_webinar", "false"),
                transfer_meeting=query_params.get("transfer_meeting", "false"),
                transfer_email=query_params.get("transfer_email", "")
            )
            return MockResponse(content=response_data, status_code=204)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.get(r"/v2/meetings/[^/]+/recordings")
    def get_meeting_recording(self, request: MockRequest) -> MockResponse:
        try:
            # Extract meeting ID from URL path
            meeting_id = request.url.path.split("/meetings/")[1].split("/recordings")[0]
            
            response_data = self._product.get_meeting_recording(meeting_id)
            return MockResponse(content=response_data)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.get(r"/v2/users/[^/]+(?!/meetings)")
    def get_user_details(self, request: MockRequest) -> MockResponse:
        try:
            # Extract user email from URL path
            user_email = request.url.path.split("/users/")[1]
            
            response_data = self._product.get_user_details(user_email)
            return MockResponse(content=response_data)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)

    @router.get(r"/v2/users/[^/]+/meetings")
    def list_meetings(self, request: MockRequest) -> MockResponse:
        try:
            # Extract user email from URL path
            user_email = request.url.path.split("/users/")[1].split("/meetings")[0]
            
            response_data = self._product.list_meetings(user_email)
            return MockResponse(content=response_data)
        except Exception as e:
            return MockResponse(content=str(e), status_code=500)