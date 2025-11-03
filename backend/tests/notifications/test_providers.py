import logging

import pytest

from app.core.config import settings
from app.notifications.base import Notification
from app.notifications.console import ConsoleProvider
from app.notifications.smtp import SMTPProvider


def test_console_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="notifications")
    provider = ConsoleProvider()
    provider.send(Notification(to="user@example.com", subject="Hello", html="<p>Hi</p>"))
    assert any("notification.send" in record.message for record in caplog.records)


def test_smtp_provider_no_config_skips(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING, logger="notifications")
    # Ensure emails are disabled
    settings.SMTP_HOST = None
    settings.EMAILS_FROM_EMAIL = None
    provider = SMTPProvider()
    provider.send(Notification(to="user@example.com", subject="Hello", html="<p>Hi</p>"))
    assert any("notification.skipped" in record.message for record in caplog.records)