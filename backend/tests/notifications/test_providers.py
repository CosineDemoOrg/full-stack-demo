from unittest.mock import MagicMock, patch

import pytest

from app.notifications.base import get_notification_provider
from app.notifications.exceptions import NotificationError
from app.notifications.providers import ConsoleNotificationProvider, SMTPNotificationProvider


def test_console_provider_logs_without_error(caplog) -> None:
    provider = ConsoleNotificationProvider()

    with caplog.at_level("INFO"):
        provider.send_email(
            email_to="user@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )

    assert any("notification_email_console" in record.message for record in caplog.records)


def test_smtp_provider_builds_smtp_options(monkeypatch) -> None:
    # Configure settings for SMTP provider
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("EMAILS_FROM_EMAIL", "from@example.com")

    provider = SMTPNotificationProvider()

    with patch("emails.Message") as message_cls:
        instance = MagicMock()
        message_cls.return_value = instance

        provider.send_email(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )

        instance.send.assert_called_once()
        args, kwargs = instance.send.call_args
        assert kwargs["to"] == "user@example.com"
        smtp_options = kwargs["smtp"]
        assert smtp_options["host"] == "smtp.example.com"
        assert smtp_options["port"] == 2525


def test_get_notification_provider_console(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATIONS_PROVIDER", "console")
    provider = get_notification_provider()
    assert isinstance(provider, ConsoleNotificationProvider)


def test_get_notification_provider_smtp_requires_config(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATIONS_PROVIDER", "smtp")
    # Ensure missing configuration triggers NotificationError on provider init
    with pytest.raises(NotificationError):
        SMTPNotificationProvider()