import types

import pytest

from app.core.config import settings
from app.notifications.providers import (
    ConsoleNotificationProvider,
    EmailMessage,
    NotificationError,
    SMTPNotificationProvider,
)


def test_console_notification_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider()
    message = EmailMessage(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    with caplog.at_level("INFO", logger="app.notifications"):
        provider.send_email(message)

    assert any(
        "notification.send" in str(record.msg)
        and record.levelname == "INFO"
        for record in caplog.records
    )


def test_smtp_notification_provider_builds_smtp_options(monkeypatch: pytest.MonkeyPatch) -> None:
    # Configure settings for SMTP
    settings.SMTP_HOST = "smtp.example.com"
    settings.SMTP_PORT = 587
    settings.SMTP_TLS = True
    settings.SMTP_SSL = False
    settings.SMTP_USER = "user"
    settings.SMTP_PASSWORD = "password"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"
    settings.EMAILS_FROM_NAME = "Example"
    # emails_enabled is a computed field, but we rely on attributes above

    sent: dict[str, object] = {}

    class DummyMessage:
        def __init__(self, subject: str, html: str, mail_from: tuple[str, str | None]):
            self.subject = subject
            self.html = html
            self.mail_from = mail_from

        def send(self, to: str, smtp: dict[str, object]) -> str:
            sent["to"] = to
            sent["smtp"] = smtp
            return "ok"

    dummy_emails = types.SimpleNamespace(Message=DummyMessage)
    monkeypatch.setattr("app.notifications.providers.emails", dummy_emails)

    provider = SMTPNotificationProvider()
    message = EmailMessage(
        email_to="dest@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    provider.send_email(message)

    assert sent["to"] == "dest@example.com"
    smtp = sent["smtp"]
    assert smtp["host"] == "smtp.example.com"
    assert smtp["port"] == 587
    assert smtp["tls"] is True
    assert smtp["user"] == "user"
    assert smtp["password"] == "password"


def test_smtp_notification_provider_raises_when_emails_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force emails_enabled to be False
    settings.SMTP_HOST = None  # type: ignore[assignment]
    settings.EMAILS_FROM_EMAIL = None  # type: ignore[assignment]

    provider = SMTPNotificationProvider()
    message = EmailMessage(
        email_to="dest@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    with pytest.raises(NotificationError):
        provider.send_email(message)