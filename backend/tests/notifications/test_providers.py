import logging

import pytest

from app.core.config import Settings
from app.notifications.providers.base import get_provider
from app.notifications.providers.console import ConsoleProvider


class DummySettings(Settings):
    NOTIFICATIONS_PROVIDER: str = "console"


def test_get_provider_console():
    settings = DummySettings()
    provider = get_provider(settings)
    assert isinstance(provider, ConsoleProvider)


def test_console_provider_logs(caplog: pytest.CaptureFixture):
    settings = DummySettings()
    provider = ConsoleProvider(settings=settings)
    caplog.set_level(logging.INFO)
    provider.send(email_to="user@example.com", subject="Test", html_content="<b>Hi</b>")
    # Expect at least one INFO log record about send
    assert any("notification.send" in r.getMessage() for r in caplog.records)