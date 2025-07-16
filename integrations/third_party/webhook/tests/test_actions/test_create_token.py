"""Comprehensive tests for the Webhook CreateToken action.

This module contains tests for the CreateToken action of the Webhook integration,
covering various success and failure scenarios using the AAA pattern.
"""

from __future__ import annotations

import json

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED

from ...actions import CreateToken
from ..common import CONFIG_PATH
from ..core.product import Webhook
from ..core.session import WebhookSession


class TestCreateToken:
    """Test class for Webhook CreateToken action."""

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "Hello World",
            "Default Content Type": "text/html",
            "Timeout": "5"
        }
    )
    def test_create_token_success(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test successful token creation.
        
        Arrange: Set up webhook product with default token creation response
        Act: Execute the CreateToken action with valid parameters
        Assert: Verify successful response, correct API call, and result JSON
        """
        # Arrange: Product will use default mock response
        # No additional setup needed as default behavior is success

        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == "https://webhook.site/token"
        assert request.method.value == "POST"

        # Assert: Verify request payload
        request_data = json.loads(request.kwargs.get("json", "{}"))
        assert request_data["default_content"] == "Hello World"
        assert request_data["default_content_type"] == "text/html"
        assert request_data["timeout"] == 5
        assert request_data["default_status"] == 200
        assert request_data["cors"] is False
        assert request_data["expiry"] is True
        assert request_data["alias"] == "my-webhook"
        assert request_data["actions"] is True

        # Assert: Verify successful output
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert "URL Created:" in action_output.results.output_message

        # Assert: Verify result JSON contains expected fields
        result_json = action_output.results.result_json
        assert result_json is not None
        assert "uuid" in result_json
        assert "webhookURL" in result_json
        assert result_json["uuid"] == "test-token-id-12345"
        assert result_json["webhookURL"] == "https://webhook.site/test-token-id-12345"

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "Custom Content",
            "Default Content Type": "application/json",
            "Timeout": "10"
        }
    )
    def test_create_token_success_custom_parameters(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test successful token creation with custom parameters.
        
        Arrange: Set up webhook product with custom parameters
        Act: Execute the CreateToken action
        Assert: Verify custom parameters are properly sent in request
        """
        # Arrange: Set up custom token response
        custom_response = {
            "uuid": "custom-token-xyz",
            "default_content": "Custom Content",
            "default_content_type": "application/json",
            "timeout": 10,
            "default_status": 200,
            "created_at": "2025-01-01 12:00:00",
        }
        webhook.set_create_token_response(custom_response)

        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        
        # Assert: Verify custom request payload
        request_data = json.loads(request.kwargs.get("json", "{}"))
        assert request_data["default_content"] == "Custom Content"
        assert request_data["default_content_type"] == "application/json"
        assert request_data["timeout"] == 10

        # Assert: Verify successful output with custom response
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        result_json = action_output.results.result_json
        assert result_json["uuid"] == "custom-token-xyz"
        assert result_json["webhookURL"] == "https://webhook.site/custom-token-xyz"

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "Test Content",
            "Default Content Type": "text/plain",
            "Timeout": "0"
        }
    )
    def test_create_token_with_zero_timeout(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token creation with zero timeout (edge case).
        
        Arrange: Set up parameters with zero timeout
        Act: Execute the CreateToken action
        Assert: Verify zero timeout is handled correctly
        """
        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        
        # Assert: Verify zero timeout is sent correctly
        request_data = json.loads(request.kwargs.get("json", "{}"))
        assert request_data["timeout"] == 0

        # Assert: Verify successful execution
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "Error Test",
            "Default Content Type": "text/html",
            "Timeout": "5"
        }
    )
    def test_create_token_failure_api_error(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token creation failure due to API error.
        
        Arrange: Set up webhook product to fail requests
        Act: Execute the CreateToken action
        Assert: Verify failure response and error handling
        """
        # Arrange: Set up API failure
        with webhook.fail_requests():
            # Act: Execute the create token action
            CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == "https://webhook.site/token"
        assert request.method.value == "POST"

        # Assert: Verify failure output
        assert action_output.results.execution_state == EXECUTION_STATE_FAILED
        assert action_output.results.result_value is False
        assert "Something went wrong." in action_output.results.output_message
        assert "Error: Failed to create token" in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "",
            "Default Content Type": "text/html",
            "Timeout": "1"
        }
    )
    def test_create_token_empty_content(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token creation with empty default content.
        
        Arrange: Set up parameters with empty content
        Act: Execute the CreateToken action
        Assert: Verify empty content is handled correctly
        """
        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        
        # Assert: Verify empty content is sent correctly
        request_data = json.loads(request.kwargs.get("json", "{}"))
        assert request_data["default_content"] == ""
        assert request_data["default_content_type"] == "text/html"

        # Assert: Verify successful execution (empty content should be allowed)
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "Large content " * 100,  # Large content
            "Default Content Type": "text/html",
            "Timeout": "30"
        }
    )
    def test_create_token_large_content(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token creation with large default content.
        
        Arrange: Set up parameters with large content
        Act: Execute the CreateToken action
        Assert: Verify large content is handled correctly
        """
        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        
        # Assert: Verify large content is sent correctly
        request_data = json.loads(request.kwargs.get("json", "{}"))
        expected_content = "Large content " * 100
        assert request_data["default_content"] == expected_content
        assert request_data["timeout"] == 30

        # Assert: Verify successful execution
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "JSON Test",
            "Default Content Type": "application/json",
            "Timeout": "15"
        }
    )
    def test_create_token_json_content_type(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token creation with JSON content type.
        
        Arrange: Set up parameters with JSON content type
        Act: Execute the CreateToken action
        Assert: Verify JSON content type is handled correctly
        """
        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        
        # Assert: Verify JSON content type is sent correctly
        request_data = json.loads(request.kwargs.get("json", "{}"))
        assert request_data["default_content_type"] == "application/json"
        assert request_data["default_content"] == "JSON Test"

        # Assert: Verify successful execution
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Default Content": "Special chars: àáâãäåæçèéêë",
            "Default Content Type": "text/html; charset=utf-8",
            "Timeout": "5"
        }
    )
    def test_create_token_special_characters(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token creation with special characters and charset.
        
        Arrange: Set up parameters with special characters
        Act: Execute the CreateToken action
        Assert: Verify special characters are handled correctly
        """
        # Act: Execute the create token action
        CreateToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        
        # Assert: Verify special characters are sent correctly
        request_data = json.loads(request.kwargs.get("json", "{}"))
        assert request_data["default_content"] == "Special chars: àáâãäåæçèéêë"
        assert request_data["default_content_type"] == "text/html; charset=utf-8"

        # Assert: Verify successful execution
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED