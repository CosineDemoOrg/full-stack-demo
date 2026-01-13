from unittest.mock import patch

from app.notifications import (
    ConsoleNotificationProvider,
    Notification,
    SMTPNotificationProvider,
)


def test_console_notification_provider_logs(caplog) -> None:
    provider = ConsoleNotificationProvider()
    notification = Notification(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    with caplog.at_level("INFO"):
        provider.send(notification)

    assert any(
        "ConsoleNotificationProvider send" in record.message for record in caplog.records
    )


def test_smtp_notification_provider_uses_send_email() -> None:
    provider = SMTPNotificationProvider()
    notification = Notification(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    with patch("app.utils.send_email") as mocked_send_email:
        provider.send(notification)

        mocked_send_email.assert_called_once_with(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )