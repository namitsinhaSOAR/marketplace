"""Comprehensive tests for the Webhook GetWebhookResponse action.

This module contains tests for the GetWebhookResponse action of the Webhook integration,
covering various success and failure scenarios using the AAA pattern.
"""

from __future__ import annotations

import json

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from soar_sdk.ScriptResult import (
    EXECUTION_STATE_COMPLETED,
    EXECUTION_STATE_FAILED,
    EXECUTION_STATE_INPROGRESS,
)

from ...actions import GetWebhookResponse
from ..common import CONFIG_PATH
from ..core.product import Webhook
from ..core.session import WebhookSession


class TestGetWebhookResponse:
    """Test class for Webhook GetWebhookResponse action."""

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-123",
            "Responses To Retrieve": "All",
            "TimeFrame": "0.01",  # Small timeframe for testing
            "Pending Condition": "TimeFrame"
        }
    )
    def test_get_webhook_response_timeframe_success_with_data(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test successful webhook response retrieval with timeframe condition and data.
        
        Arrange: Set up webhook product with request data for the token
        Act: Execute the GetWebhookResponse action with timeframe condition
        Assert: Verify successful response with request data
        """
        # Arrange: Set up mock request data for the token
        test_token_id = "test-token-123"
        mock_request_data = {
            "uuid": "request-uuid-123",
            "type": "web",
            "token_id": test_token_id,
            "ip": "192.168.1.1",
            "hostname": "webhook.site",
            "method": "GET",
            "user_agent": "Mozilla/5.0 (test browser)",
            "content": "",
            "query": {"param1": "value1"},
            "headers": {"Content-Type": "application/json"},
            "url": f"https://webhook.site/{test_token_id}",
            "size": 0,
            "files": [],
            "created_at": "2025-01-01 12:00:00",
            "updated_at": "2025-01-01 12:00:00",
            "sorting": 1640995200000,
            "custom_action_output": []
        }
        
        webhook.add_request_data(test_token_id, mock_request_data)

        # Act: Execute the get webhook response action (first run)
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.path == f"/token/{test_token_id}/requests"
        assert request.method.value == "GET"

        # Assert: Verify successful output
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert f"Fetched requests for token ID <{test_token_id}>" in action_output.results.output_message

        # Assert: Verify result JSON contains expected request data
        result_json = action_output.results.result_json
        assert result_json is not None
        assert result_json["requests_type"] == "all"
        assert len(result_json["data"]) == 1
        assert result_json["data"][0]["uuid"] == "request-uuid-123"
        assert result_json["total"] == 1

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-456",
            "Responses To Retrieve": "Latest",
            "TimeFrame": "0.01",
            "Pending Condition": "TimeFrame"
        }
    )
    def test_get_webhook_response_timeframe_no_data(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test webhook response retrieval with timeframe condition but no data.
        
        Arrange: Set up webhook product with no request data for the token
        Act: Execute the GetWebhookResponse action with timeframe condition
        Assert: Verify successful completion but no requests found message
        """
        # Arrange: No additional setup needed (no request data)
        test_token_id = "test-token-456"

        # Act: Execute the get webhook response action (first run)
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.path == f"/token/{test_token_id}/requests"

        # Assert: Verify successful completion with no data message
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert "No requests were found" in action_output.results.output_message

        # Assert: Verify result JSON shows no data
        result_json = action_output.results.result_json
        assert result_json is not None
        assert result_json["requests_type"] == "latest"
        assert len(result_json["data"]) == 0

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-789",
            "Responses To Retrieve": "All",
            "TimeFrame": "5",  # Longer timeframe
            "Pending Condition": "TimeFrame"
        }
    )
    def test_get_webhook_response_timeframe_in_progress(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test webhook response with timeframe condition showing in progress.
        
        Arrange: Set up webhook product with longer timeframe
        Act: Execute the GetWebhookResponse action in first run
        Assert: Verify in progress status during timeframe wait
        """
        # Act: Execute the get webhook response action (first run with long timeframe)
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify action is in progress (timeframe not finished)
        assert action_output.results.execution_state == EXECUTION_STATE_INPROGRESS
        assert "Awaiting Timout" in action_output.results.output_message
        assert "Time passed:" in action_output.results.output_message

        # Assert: Verify result value contains timing information
        result_value = json.loads(action_output.results.result_value)
        assert "timeframe" in result_value
        assert "start_time" in result_value

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-await",
            "Responses To Retrieve": "All",
            "TimeFrame": "5",
            "Pending Condition": "AwaitClick"
        }
    )
    def test_get_webhook_response_await_click_with_data(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test webhook response with await click condition and data available.
        
        Arrange: Set up webhook product with request data for await click
        Act: Execute the GetWebhookResponse action with await click condition
        Assert: Verify successful completion when data is available
        """
        # Arrange: Set up mock request data for await click scenario
        test_token_id = "test-token-await"
        mock_request_data = {
            "uuid": "click-request-123",
            "type": "web",
            "token_id": test_token_id,
            "method": "POST",
            "user_agent": "PostmanRuntime/7.26.8",
            "content": '{"message": "clicked"}',
            "created_at": "2025-01-01 12:05:00",
        }
        
        webhook.add_request_data(test_token_id, mock_request_data)

        # Act: Execute the get webhook response action
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.path == f"/token/{test_token_id}/requests"

        # Assert: Verify successful completion
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED
        assert action_output.results.result_value is True
        assert f"Successfully fetched first requests for token ID <{test_token_id}>" in action_output.results.output_message

        # Assert: Verify result JSON contains the click data
        result_json = action_output.results.result_json
        assert result_json is not None
        assert len(result_json["data"]) == 1
        assert result_json["data"][0]["uuid"] == "click-request-123"

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-no-click",
            "Responses To Retrieve": "Latest",
            "TimeFrame": "5",
            "Pending Condition": "AwaitClick"
        }
    )
    def test_get_webhook_response_await_click_no_data(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test webhook response with await click condition but no data.
        
        Arrange: Set up webhook product with no request data
        Act: Execute the GetWebhookResponse action with await click condition
        Assert: Verify in progress status while waiting for click
        """
        # Arrange: No additional setup needed (no request data)
        test_token_id = "test-token-no-click"

        # Act: Execute the get webhook response action
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify the correct API call was made
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.path == f"/token/{test_token_id}/requests"

        # Assert: Verify in progress status (still waiting for click)
        assert action_output.results.execution_state == EXECUTION_STATE_INPROGRESS
        assert action_output.results.result_value is True
        assert f"Still waiting for first request for token ID <{test_token_id}>" in action_output.results.output_message

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-filter",
            "Responses To Retrieve": "All",
            "TimeFrame": "0.01",
            "Pending Condition": "TimeFrame"
        }
    )
    def test_get_webhook_response_filter_slack_requests(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test that Slack bot requests are filtered out correctly.
        
        Arrange: Set up webhook product with both regular and Slack bot requests
        Act: Execute the GetWebhookResponse action
        Assert: Verify only non-Slack requests are returned
        """
        # Arrange: Set up mixed request data (including Slack bot request)
        test_token_id = "test-token-filter"
        
        regular_request = {
            "uuid": "regular-request-123",
            "type": "web",
            "token_id": test_token_id,
            "user_agent": "Mozilla/5.0 (normal browser)",
            "method": "GET",
            "created_at": "2025-01-01 12:00:00",
        }
        
        slack_request = {
            "uuid": "slack-request-456",
            "type": "web", 
            "token_id": test_token_id,
            "user_agent": "Slackbot 1.0 (+https://api.slack.com/robots)",
            "method": "GET",
            "created_at": "2025-01-01 12:01:00",
        }
        
        webhook.add_request_data(test_token_id, regular_request)
        webhook.add_request_data(test_token_id, slack_request)

        # Act: Execute the get webhook response action
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify successful completion
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED

        # Assert: Verify only non-Slack request is returned
        result_json = action_output.results.result_json
        assert result_json is not None
        assert len(result_json["data"]) == 1
        assert result_json["data"][0]["uuid"] == "regular-request-123"
        assert result_json["total"] == 1

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-latest",
            "Responses To Retrieve": "Latest",
            "TimeFrame": "0.01",
            "Pending Condition": "TimeFrame"
        }
    )
    def test_get_webhook_response_latest_only(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test retrieving only the latest request when multiple exist.
        
        Arrange: Set up webhook product with multiple requests
        Act: Execute the GetWebhookResponse action with 'Latest' parameter
        Assert: Verify only the latest request is returned
        """
        # Arrange: Set up multiple request data
        test_token_id = "test-token-latest"
        
        older_request = {
            "uuid": "older-request-123",
            "type": "web",
            "token_id": test_token_id,
            "user_agent": "Mozilla/5.0 (browser)",
            "created_at": "2025-01-01 11:00:00",
        }
        
        newer_request = {
            "uuid": "newer-request-456",
            "type": "web",
            "token_id": test_token_id,
            "user_agent": "Mozilla/5.0 (browser)",
            "created_at": "2025-01-01 12:00:00",
        }
        
        webhook.add_request_data(test_token_id, older_request)
        webhook.add_request_data(test_token_id, newer_request)

        # Act: Execute the get webhook response action
        GetWebhookResponse.main(is_first_run=True)

        # Assert: Verify successful completion
        assert action_output.results.execution_state == EXECUTION_STATE_COMPLETED

        # Assert: Verify only the latest (last added) request is returned
        result_json = action_output.results.result_json
        assert result_json is not None
        assert result_json["requests_type"] == "latest"
        assert len(result_json["data"]) == 1
        assert result_json["data"][0]["uuid"] == "newer-request-456"

    @set_metadata(
        integration_config_file_path=CONFIG_PATH,
        parameters={
            "Token ID": "test-token-error",
            "Responses To Retrieve": "All",
            "TimeFrame": "0.01",
            "Pending Condition": "TimeFrame"
        }
    )
    def test_get_webhook_response_api_error(
        self,
        script_session: WebhookSession,
        action_output: MockActionOutput,
        webhook: Webhook,
    ) -> None:
        """Test webhook response retrieval failure due to API error.
        
        Arrange: Set up webhook product to fail requests
        Act: Execute the GetWebhookResponse action
        Assert: Verify failure response and error handling
        """
        # Arrange: Set up API failure
        test_token_id = "test-token-error"
        
        with webhook.fail_requests():
            # Act: Execute the get webhook response action
            try:
                GetWebhookResponse.main(is_first_run=True)
            except Exception:
                # The action re-raises the exception, which is expected behavior
                pass

        # Assert: Verify the correct API call was attempted
        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.path == f"/token/{test_token_id}/requests"

        # Assert: Verify failure output
        assert action_output.results.execution_state == EXECUTION_STATE_FAILED
        assert action_output.results.result_value is False
        assert f"Could not fetch information regarding token ID <{test_token_id}>" in action_output.results.output_message