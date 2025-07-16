"""Pytest configuration and fixtures for Webhook integration tests."""

from __future__ import annotations

import pytest

from .core.product import Webhook
from .core.session import WebhookSession


@pytest.fixture
def webhook() -> Webhook:
    """Provide a Webhook product instance for testing.
    
    Returns:
        Webhook: A fresh Webhook product instance for each test.
    """
    product = Webhook()
    # Clear any previous state
    product.clear_all_data()
    return product


@pytest.fixture
def script_session(webhook: Webhook) -> WebhookSession:
    """Provide a mock session with Webhook product integration.
    
    Args:
        webhook: The Webhook product instance.
        
    Returns:
        WebhookSession: Mock session configured with the Webhook product.
    """
    session = WebhookSession(mock_product=webhook)
    return session