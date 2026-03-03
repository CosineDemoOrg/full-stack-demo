from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    NotificationSendError,
    SmtpNotificationProvider,
    get_provider,
)


def test_console_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider()
    with caplog.at_level("INFO"):
        provider.send_email(
            email_to="user@example.com",
            subject="Test",
            html_content="<p>Hi</p>",
        )
    assert any("notification.send.console" in str(record.msg) for record in caplog.records)


def test_smtp_provider_uses_emails_library() -> None:
    provider = SmtpNotificationProvider()
    with (
        patch("app.notifications.providers.emails.Message") as message_cls,
        patch.object(settings, "emails_enabled", True),
    ):
        message_instance = MagicMock()
        message_cls.return_value = message_instance

        provider.send_email(
            email_to="user@example.com",
            subject="Test",
            html_content="<p>Hi</p>",
        )

        message_cls.assert_called_once()
        message_instance.send.assert_called_once()


def test_smtp_provider_raises_on_error() -> None:
    provider = SmtpNotificationProvider()
    with (
        patch("app.notifications.providers.emails.Message") as message_cls,
        patch.object(settings, "emails_enabled", True),
    ):
        message_instance = MagicMock()
        message_instance.send.side_effect = RuntimeError("smtp error")
        message_cls.return_value = message_instance

        with pytest.raises(NotificationSendError):
            provider.send_email(
                email_to="user@example.com",
                subject="Test",
                html_content="<p>Hi</p>",
            )


def test_get_provider_console() -> None:
    with patch.object(settings, "NOTIFICATIONS_PROVIDER", "console"):
        provider = get_provider()
    assert isinstance(provider, ConsoleNotificationProvider)


def test_get_provider_smtp() -> None:
    with patch.object(settings, "NOTIFICATIONS_PROVIDER", "smtp"):
        provider = get_provider()
    assert isinstance(provider, SmtpNotificationProvider)