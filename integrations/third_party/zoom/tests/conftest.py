from __future__ import annotations

import pytest
from integration_testing.common import use_live_api
from TIPCommon.base.utils import CreateSession

from .core.product import Zoom
from .core.session import ZoomSession

pytest_plugins = ("integration_testing.conftest",)


@pytest.fixture
def zoom() -> Zoom:
    return Zoom()


@pytest.fixture(autouse=True)
def script_session(
    monkeypatch: pytest.MonkeyPatch,
    zoom: Zoom,
) -> ZoomSession:
    """Mock zoom scripts' session and get back an object to view request history"""
    session: ZoomSession = ZoomSession(zoom)

    if not use_live_api():
        monkeypatch.setattr(CreateSession, "create_session", lambda: session)
        monkeypatch.setattr("requests.Session", lambda: session)

    return session