from unittest.mock import patch

from app.notifications import (
    ConsoleNotificationProvider,
    SmtpNotificationProvider,
    send_notification_email,
)


def test_console_notification_provider_logs() -> None:
    provider = ConsoleNotificationProvider()
    # Just ensure it doesn't raise and calls logger
    with patch("app.notifications.logger") as logger:
        provider.send_email(email_to="user@example.com", subject="Subject", html_content="Body")
        logger.info.assert_called_once()


def test_smtp_notification_provider_uses_emails_message_send() -> None:
    provider = SmtpNotificationProvider()
    with (
        patch("app.core.config.settings.emails_enabled", True),
        patch("emails.Message.send", return_value="ok") as send_mock,
    ):
        provider.send_email(email_to="user@example.com", subject="Subject", html_content="Body")
        send_mock.assert_called_once()


def test_send_notification_email_uses_configured_provider_console() -> None:
    with (
        patch("app.core.config.settings.NOTIFICATIONS_PROVIDER", "console"),
        patch("app.notifications.ConsoleNotificationProvider.send_email") as console_send,
    ):
        send_notification_email(email_to="user@example.com", subject="Subject", html_content="Body")
        console_send.assert_called_once()


def test_send_notification_email_uses_configured_provider_smtp() -> None:
    with (
        patch("app.core.config.settings.NOTIFICATIONS_PROVIDER", "smtp"),
        patch("app.notifications.SmtpNotificationProvider.send_email") as smtp_send,
    ):
        send_notification_email(email_to="user@example.com", subject="Subject", html_content="Body")
        smtp_send.assert_called_once()