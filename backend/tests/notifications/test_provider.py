import logging

import pytest

from app.core.config import settings
from app.notifications.provider import EmailMessage, get_provider


def test_console_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    # Force console provider
    settings.NOTIFICATIONS_PROVIDER = "console"  # type: ignore
    provider = get_provider()
    caplog.set_level(logging.INFO)
    provider.send_email(
        EmailMessage(to="user@example.com", subject="Test", html="<p>Hello</p>")
    )
    # Check that an info log was produced with expected fields
    assert any(
        "notification_email_scheduled" in record.getMessage() for record in caplog.records
    )