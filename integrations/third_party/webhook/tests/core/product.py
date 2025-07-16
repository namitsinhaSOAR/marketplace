"""Product mock for Webhook integration testing.

This module provides the Webhook product mock that simulates API responses
and manages the state for testing webhook-related operations.
"""

from __future__ import annotations

import contextlib
import dataclasses
from typing import Any

from TIPCommon.types import SingleJson


@dataclasses.dataclass(slots=True)
class Webhook:
    """Mock Webhook product for testing API interactions.
    
    This class simulates the webhook.site API responses and provides
    methods to control mock behavior for comprehensive testing.
    """
    
    # Response storage for various API endpoints
    _connectivity_response: bool = True
    _create_token_response: SingleJson | None = None
    _get_requests_response: SingleJson | None = None
    _delete_token_response: int = 200
    
    # State management
    _fail_requests_active: bool = False
    _tokens: dict[str, SingleJson] = dataclasses.field(default_factory=dict)
    _requests_data: dict[str, list[SingleJson]] = dataclasses.field(default_factory=dict)

    @contextlib.contextmanager
    def fail_requests(self) -> None:
        """Context manager to simulate API request failures.
        
        When used, all API calls within the context will fail,
        allowing testing of error handling scenarios.
        """
        self._fail_requests_active = True
        try:
            yield
        finally:
            self._fail_requests_active = False

    def test_connectivity(self) -> bool:
        """Mock the test_connectivity API call.
        
        Returns:
            bool: True if connectivity is successful, False otherwise.
            
        Raises:
            Exception: If fail_requests is active.
        """
        if self._fail_requests_active:
            raise Exception("Connection failed")
        return self._connectivity_response

    def set_connectivity_response(self, success: bool) -> None:
        """Set the response for connectivity tests.
        
        Args:
            success: Whether connectivity should succeed.
        """
        self._connectivity_response = success

    def create_token(self, def_content: str, def_content_type: str, timeout: int) -> SingleJson:
        """Mock the create_token API call.
        
        Args:
            def_content: Default content for the webhook.
            def_content_type: Content type for the webhook.
            timeout: Timeout in seconds.
            
        Returns:
            SingleJson: Mock token creation response.
            
        Raises:
            Exception: If fail_requests is active.
        """
        if self._fail_requests_active:
            raise Exception("Failed to create token")
            
        if self._create_token_response is not None:
            return self._create_token_response
            
        # Default mock response
        token_id = "test-token-id-12345"
        response = {
            "uuid": token_id,
            "redirect": False,
            "alias": "my-webhook",
            "actions": True,
            "cors": False,
            "expiry": True,
            "timeout": timeout,
            "premium": False,
            "user_id": None,
            "password": False,
            "ip": "127.0.0.1",
            "user_agent": "python-requests/2.32.3",
            "default_content": def_content,
            "default_status": 200,
            "default_content_type": def_content_type,
            "premium_expires_at": None,
            "created_at": "2025-01-01 12:00:00",
            "updated_at": "2025-01-01 12:00:00",
        }
        
        # Store the token for future reference
        self._tokens[token_id] = response
        return response

    def set_create_token_response(self, response: SingleJson) -> None:
        """Set a custom response for token creation.
        
        Args:
            response: Custom token creation response.
        """
        self._create_token_response = response

    def get_requests(self, token_id: str, res_choice: str) -> SingleJson:
        """Mock the get_requests API call.
        
        Args:
            token_id: ID of the token to inspect.
            res_choice: Choice of which requests to get ('all' or 'latest').
            
        Returns:
            SingleJson: Mock requests response.
            
        Raises:
            Exception: If fail_requests is active.
        """
        if self._fail_requests_active:
            raise Exception("Failed to get requests")
            
        if self._get_requests_response is not None:
            return self._get_requests_response
            
        # Get stored requests for this token
        requests_data = self._requests_data.get(token_id, [])
        
        # Filter out Slack bot requests (as done in the real implementation)
        filtered_data = [
            req for req in requests_data 
            if "Slack" not in req.get("user_agent", "")
        ]
        
        # Apply latest filter if requested
        if res_choice.lower() == "latest" and filtered_data:
            filtered_data = [filtered_data[-1]]
            
        response = {
            "requests_type": res_choice.lower(),
            "data": filtered_data,
            "total": len(filtered_data),
            "per_page": 50,
            "current_page": 1,
            "is_last_page": True,
            "from": 1 if filtered_data else 0,
            "to": len(filtered_data),
        }
        
        return response

    def set_get_requests_response(self, response: SingleJson) -> None:
        """Set a custom response for get_requests.
        
        Args:
            response: Custom get requests response.
        """
        self._get_requests_response = response

    def add_request_data(self, token_id: str, request_data: SingleJson) -> None:
        """Add mock request data for a token.
        
        Args:
            token_id: ID of the token.
            request_data: Request data to add.
        """
        if token_id not in self._requests_data:
            self._requests_data[token_id] = []
        self._requests_data[token_id].append(request_data)

    def delete_token(self, token_id: str) -> int:
        """Mock the delete_token API call.
        
        Args:
            token_id: ID of the token to delete.
            
        Returns:
            int: HTTP status code.
            
        Raises:
            Exception: If fail_requests is active.
        """
        if self._fail_requests_active:
            raise Exception("Failed to delete token")
            
        # Remove token from stored tokens
        if token_id in self._tokens:
            del self._tokens[token_id]
        if token_id in self._requests_data:
            del self._requests_data[token_id]
            
        return self._delete_token_response

    def set_delete_token_response(self, status_code: int) -> None:
        """Set the response status code for token deletion.
        
        Args:
            status_code: HTTP status code to return.
        """
        self._delete_token_response = status_code

    def clear_all_data(self) -> None:
        """Clear all stored tokens and requests data."""
        self._tokens.clear()
        self._requests_data.clear()
        self._create_token_response = None
        self._get_requests_response = None
        self._connectivity_response = True
        self._delete_token_response = 200