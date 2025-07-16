"""Session mock for Webhook integration testing.

This module provides the WebhookSession class that handles mock HTTP requests
and routes them to appropriate methods based on URL patterns.
"""

from __future__ import annotations

import json
from typing import Any

from integration_testing import router
from integration_testing.common import get_request_payload
from integration_testing.request import MockRequest
from integration_testing.requests.response import MockResponse
from integration_testing.requests.session import MockSession, RouteFunction

from .product import Webhook


class WebhookSession(MockSession[MockRequest, MockResponse, Webhook]):
    """Mock session for Webhook API requests.
    
    This class handles routing of mock HTTP requests to appropriate
    handler methods that simulate the webhook.site API behavior.
    """

    def get_routed_functions(self) -> list[RouteFunction]:
        """Get all routed functions for this session.
        
        Returns:
            List of functions that handle specific API routes.
        """
        return [
            self.test_connectivity,
            self.create_token,
            self.get_requests,
            self.delete_token,
        ]

    @router.get(r"^https://webhook\.site/?$")
    def test_connectivity(self, request: MockRequest) -> MockResponse:
        """Handle connectivity test requests.
        
        Args:
            request: The mock HTTP request.
            
        Returns:
            MockResponse: Response indicating connectivity status.
        """
        try:
            success = self._product.test_connectivity()
            if success:
                return MockResponse(
                    content="Webhook.site is operational",
                    status_code=200
                )
            else:
                return MockResponse(
                    content="Service unavailable",
                    status_code=503
                )
        except Exception as e:
            return MockResponse(
                content=str(e),
                status_code=500
            )

    @router.post(r"^https://webhook\.site/token/?$")
    def create_token(self, request: MockRequest) -> MockResponse:
        """Handle token creation requests.
        
        Args:
            request: The mock HTTP request.
            
        Returns:
            MockResponse: Response with token creation data.
        """
        try:
            payload: dict[str, Any] = get_request_payload(request)
            
            # Extract parameters from payload
            def_content = payload.get("default_content", "Hello world")
            def_content_type = payload.get("default_content_type", "text/html")
            timeout = payload.get("timeout", 0)
            
            response_data = self._product.create_token(
                def_content, def_content_type, timeout
            )
            
            return MockResponse(
                content=json.dumps(response_data),
                status_code=200,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            error_response = {"error": str(e)}
            return MockResponse(
                content=json.dumps(error_response),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )

    @router.get(r"^https://webhook\.site/token/([^/]+)/requests/?$")
    def get_requests(self, request: MockRequest) -> MockResponse:
        """Handle get requests for a specific token.
        
        Args:
            request: The mock HTTP request.
            
        Returns:
            MockResponse: Response with request data for the token.
        """
        try:
            # Extract token_id from URL path
            path_parts = request.url.path.strip('/').split('/')
            token_id = path_parts[1]  # token/{token_id}/requests
            
            # Default to "all" requests
            res_choice = "all"
            
            response_data = self._product.get_requests(token_id, res_choice)
            
            return MockResponse(
                content=json.dumps(response_data),
                status_code=200,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            error_response = {"error": str(e)}
            return MockResponse(
                content=json.dumps(error_response),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )

    @router.delete(r"^https://webhook\.site/token/([^/]+)/?$")
    def delete_token(self, request: MockRequest) -> MockResponse:
        """Handle token deletion requests.
        
        Args:
            request: The mock HTTP request.
            
        Returns:
            MockResponse: Response indicating deletion status.
        """
        try:
            # Extract token_id from URL path
            path_parts = request.url.path.strip('/').split('/')
            token_id = path_parts[1]  # token/{token_id}
            
            status_code = self._product.delete_token(token_id)
            
            return MockResponse(
                content="",
                status_code=status_code
            )
        except Exception as e:
            error_response = {"error": str(e)}
            return MockResponse(
                content=json.dumps(error_response),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )