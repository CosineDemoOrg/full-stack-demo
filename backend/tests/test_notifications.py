from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    SMTPNotificationProvider,
    get_notification_provider,
)


def test_console_notification_provider_logs_email(caplog) -> None:
    provider = ConsoleNotificationProvider()

    with caplog.at_level("INFO"):
        provider.send_email(
            email_to="user@example.com",
            subject="Test Subject",
            html_content="<p>Test</p>",
        )

    assert any(
        "Console notification provider sending email" in message
        for message in caplog.text.splitlines()
    )


def test_smtp_notification_provider_sends_email() -> None:
    provider = SMTPNotificationProvider()

    with (
        patch("app.notifications.emails.Message") as message_cls,
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_PORT", 587),
        patch("app.core.config.settings.EMAILS_FROM_EMAIL", "noreply@example.com"),
    ):
        message_instance = MagicMock()
        message_cls.return_value = message_instance

        provider.send_email(
            email_to="user@example.com",
            subject="Test Subject",
            html_content="<p>Test</p>",
        )

        message_cls.assert_called_once_with(
            subject="Test Subject",
            html="<p>Test</p>",
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        message_instance.send.assert_called_once()


def test_get_notification_provider_console(monkeypatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console", raising=False)

    provider = get_notification_provider()

    assert isinstance(provider, ConsoleNotificationProvider)


def test_get_notification_provider_smtp(monkeypatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp", raising=False)

    provider = get_notification_provider()

    assert isinstance(provider, SMTPNotificationProvider)
