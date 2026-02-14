import logging
from unittest.mock import patch, MagicMock

import pytest

from app.core.config import settings
from app.notifications.providers import ConsoleProvider, SmtpProvider, NotificationError


def test_console_provider_logs(caplog):
    provider = ConsoleProvider()
    with caplog.at_level(logging.INFO, logger="app.notifications"):
        provider.send_email(email_to="user@example.com", subject="Subj", html_content="<p>Hi</p>")
    # Ensure a record was emitted by our logger
    records = [r for r in caplog.records if r.name == "app.notifications"]
    assert records, "No notification logs captured"


def test_smtp_provider_sends(monkeypatch):
    # Ensure SMTP settings are set on settings object
    settings.SMTP_HOST = "smtp.example.com"
    settings.SMTP_PORT = 587
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"

    provider = SmtpProvider()
    with patch("app.notifications.providers.emails.Message") as MockMessage:
        instance: MagicMock = MockMessage.return_value
        instance.send.return_value = {"status": "ok"}
        provider.send_email(
            email_to="user@example.com", subject="Test", html_content="<p>Body</p>"
        )
        instance.send.assert_called_once()


def test_smtp_provider_raises_without_config():
    # Remove config
    settings.SMTP_HOST = None
    settings.EMAILS_FROM_EMAIL = None
    provider = SmtpProvider()
    with pytest.raises(NotificationError):
        provider.send_email(email_to="u@e.com", subject="s", html_content="h")