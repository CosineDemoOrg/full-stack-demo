from unittest.mock import MagicMock

import pytest

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    SMTPNotificationProvider,
    get_notification_provider,
    send_email_notification,
)


def test_get_notification_provider_console(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console", raising=False)
    provider = get_notification_provider()
    assert isinstance(provider, ConsoleNotificationProvider)


def test_get_notification_provider_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp", raising=False)
    provider = get_notification_provider()
    assert isinstance(provider, SMTPNotificationProvider)


def test_console_notification_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider()
    with caplog.at_level("INFO"):
        provider.send_email(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )

    assert any("Console notification email" in record.getMessage() for record in caplog.records)


def test_smtp_notification_provider_sends_email(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure emails are considered enabled
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com", raising=False)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "no-reply@example.com", raising=False)

    sent = {}

    class DummyMessage:
        def __init__(self, subject: str, html: str, mail_from: object) -> None:
            sent["subject"] = subject
            sent["html"] = html
            sent["mail_from"] = mail_from

        def send(self, to: str, smtp: dict[str, object]) -> str:
            sent["to"] = to
            sent["smtp"] = smtp
            return "ok"

    monkeypatch.setattr("app.notifications.emails.Message", DummyMessage)

    provider = SMTPNotificationProvider()
    provider.send_email(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    assert sent["to"] == "user@example.com"
    assert sent["subject"] == "Subject"
    assert sent["html"] == "<p>Body</p>"
    assert "smtp" in sent


def test_smtp_notification_provider_raises_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Ensure emails are considered enabled
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com", raising=False)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "no-reply@example.com", raising=False)

    class FailingDummyMessage:
        def __init__(self, subject: str, html: str, mail_from: object) -> None:
            pass

        def send(self, to: str, smtp: dict[str, object]) -> None:
            raise RuntimeError("SMTP failure")

    monkeypatch.setattr("app.notifications.emails.Message", FailingDummyMessage)

    provider = SMTPNotificationProvider()
    with pytest.raises(RuntimeError):
        provider.send_email(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )


def test_send_email_notification_uses_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_provider = MagicMock()
    monkeypatch.setattr(
        "app.notifications.get_notification_provider",
        lambda: mock_provider,
    )

    send_email_notification(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    mock_provider.send_email.assert_called_once_with(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )