from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    SMTPNotificationProvider,
)


def test_console_notification_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider()
    with caplog.at_level("INFO"):
        provider.send_email(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )
    assert any("ConsoleNotificationProvider - email:" in message for message in caplog.text.splitlines())


def test_smtp_notification_provider_sends_email() -> None:
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.EMAILS_FROM_EMAIL", "no-reply@example.com"),
        patch("app.core.config.settings.EMAILS_FROM_NAME", "Example"),
        patch("app.notifications.emails.Message") as message_cls,
    ):
        message_instance = MagicMock()
        message_cls.return_value = message_instance

        provider = SMTPNotificationProvider()
        provider.send_email(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )

        message_cls.assert_called_once()
        message_instance.send.assert_called_once()