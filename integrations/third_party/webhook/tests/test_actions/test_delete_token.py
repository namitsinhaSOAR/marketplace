"""Comprehensive tests for the Webhook DeleteToken action.

This module contains tests for the DeleteToken action of the Webhook integration,
covering various success and failure scenarios using the AAA pattern.
"""

from __future__ import annotations

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from soar_sdk.ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED

from ...actions import DeleteToken
from ..common import CONFIG_PATH
from ..core.product import Webhook
from ..core.session import WebhookSession


class TestDeleteToken:
    """Test class for Webhook DeleteToken action."""

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-delete-123"
        }
    )
    def test_delete_token_success(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test successful token deletion.
        
        Arrange: Set up webhook product with default successful delete response
        Act: Execute the DeleteToken action with valid token ID
        Assert: Verify successful response and correct API call
        """
        # Arrange: Product will use default mock response (200 status code)
        test_token_id = "test-token-delete-123"

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == f"https://webhook.site/token/{test_token_id}"
        assert request.method.value == "DELETE"

        # Assert: Verify successful output
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert f"Token <{test_token_id}> was successfully deleted." in action_output.results.output_message
        assert "Deletion status: 200" in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-delete-456"
        }
    )
    def test_delete_token_success_with_custom_status(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test successful token deletion with custom HTTP status code.
        
        Arrange: Set up webhook product with custom delete response status
        Act: Execute the DeleteToken action
        Assert: Verify custom status code is reflected in output
        """
        # Arrange: Set up custom delete response status
        test_token_id = "test-token-delete-456"
        webhook.set_delete_token_response(204)  # No Content status

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == f"https://webhook.site/token/{test_token_id}"
        assert request.method.value == "DELETE"

        # Assert: Verify successful output with custom status
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert f"Token <{test_token_id}> was successfully deleted." in action_output.results.output_message
        assert "Deletion status: 204" in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-delete-error"
        }
    )
    def test_delete_token_failure_api_error(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token deletion failure due to API error.
        
        Arrange: Set up webhook product to fail requests
        Act: Execute the DeleteToken action
        Assert: Verify failure response and error handling
        """
        # Arrange: Set up API failure
        test_token_id = "test-token-delete-error"
        
        with webhook.fail_requests():
            # Act: Execute the delete token action
            DeleteToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == f"https://webhook.site/token/{test_token_id}"
        assert request.method.value == "DELETE"

        # Assert: Verify failure output
        assert action_output.results.execution_state == EXECUTION_STATE_FAILED
        assert action_output.results.result_value is False
        assert f"Something went wrong deleting token <{test_token_id}>." in action_output.results.output_message
        assert "Error: Failed to delete token" in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "very-long-token-id-with-special-chars-123456789-abcdef-!@#$%^&*()"
        }
    )
    def test_delete_token_with_special_token_id(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token deletion with special characters in token ID.
        
        Arrange: Set up webhook product with default delete response
        Act: Execute the DeleteToken action with special character token ID
        Assert: Verify special characters are handled correctly in URL
        """
        # Arrange: Product will use default mock response
        test_token_id = "very-long-token-id-with-special-chars-123456789-abcdef-!@#$%^&*()"

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify the correct API call was made with special characters
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        # Note: URL encoding may be applied to special characters
        assert f"/token/{test_token_id}" in request.url.path or f"/token/{test_token_id}" in request.url.geturl()
        assert request.method.value == "DELETE"

        # Assert: Verify successful output
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert f"Token <{test_token_id}> was successfully deleted." in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": ""  # Empty token ID
        }
    )
    def test_delete_token_empty_token_id(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token deletion with empty token ID.
        
        Arrange: Set up webhook product with default delete response
        Act: Execute the DeleteToken action with empty token ID
        Assert: Verify empty token ID is handled (may succeed or fail based on API)
        """
        # Arrange: Product will use default mock response
        test_token_id = ""

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == "https://webhook.site/token/"
        assert request.method.value == "DELETE"

        # Assert: Verify output (behavior may vary with empty token)
        # The action should still complete since our mock allows it
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "   whitespace-token-123   "  # Token with whitespace
        }
    )
    def test_delete_token_whitespace_token_id(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token deletion with whitespace in token ID.
        
        Arrange: Set up webhook product with default delete response
        Act: Execute the DeleteToken action with whitespace in token ID
        Assert: Verify whitespace is stripped (based on action implementation)
        """
        # Arrange: Product will use default mock response
        # Note: The action strips whitespace with .strip()

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify the correct API call was made with stripped token ID
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        # The action should strip whitespace
        assert request.url.geturl() == "https://webhook.site/token/whitespace-token-123"
        assert request.method.value == "DELETE"

        # Assert: Verify successful output
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert "Token <whitespace-token-123> was successfully deleted." in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "uuid-format-12345678-1234-1234-1234-123456789abc"
        }
    )
    def test_delete_token_uuid_format(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test token deletion with UUID format token ID.
        
        Arrange: Set up webhook product with default delete response
        Act: Execute the DeleteToken action with UUID format token ID
        Assert: Verify UUID format is handled correctly
        """
        # Arrange: Product will use default mock response
        test_token_id = "uuid-format-12345678-1234-1234-1234-123456789abc"

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.geturl() == f"https://webhook.site/token/{test_token_id}"
        assert request.method.value == "DELETE"

        # Assert: Verify successful output
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert f"Token <{test_token_id}> was successfully deleted." in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-repeated-delete"
        }
    )
    def test_delete_token_repeated_calls(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test that delete token action only makes one API call.
        
        Arrange: Set up webhook product with successful delete response
        Act: Execute the DeleteToken action
        Assert: Verify only one API call is made
        """
        # Arrange: Set up successful delete response
        test_token_id = "test-token-repeated-delete"

        # Act: Execute the delete token action
        DeleteToken.main()

        # Assert: Verify exactly one API call was made
        assert len(script_session.request_history) == 1
        
        # Act: Clear history and run again to verify idempotency
        script_session.clear_record()
        action_output.flush()
        
        DeleteToken.main()
        
        # Assert: Verify still only one call per execution
        assert len(script_session.request_history) == 1
        
        # Assert: Verify the second call was also successful
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True