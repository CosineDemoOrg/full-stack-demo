from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    SmtpNotificationProvider,
    get_notification_provider,
)


def test_console_provider_logs_email(caplog) -> None:
    provider = ConsoleNotificationProvider()

    with caplog.at_level("INFO"):
        provider.send_email(email_to="test@example.com", subject="Subject", html_content="<p>Body</p>")

    assert any("Console email notification" in message for message in caplog.text.splitlines())


def test_smtp_provider_uses_emails_library(monkeypatch) -> None:
    class DummyMessage:
        def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
            self.kwargs = kwargs
            self.sent_to: str | None = None
            self.smtp_options: dict[str, object] | None = None

        def send(self, to: str, smtp: dict[str, object]) -> str:  # type: ignore[no-untyped-def]
            self.sent_to = to
            self.smtp_options = smtp
            return "ok"

    dummy_emails = SimpleNamespace(Message=DummyMessage)
    monkeypatch.setattr("app.notifications.emails", dummy_emails, raising=False)

    provider = SmtpNotificationProvider()

    # Ensure emails are enabled for the assertion inside the provider
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "from@example.com")

    provider.send_email(email_to="user@example.com", subject="Hello", html_content="<p>Hi</p>")


def test_get_notification_provider_console(monkeypatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console")

    provider = get_notification_provider()

    assert isinstance(provider, ConsoleNotificationProvider)


def test_get_notification_provider_smtp(monkeypatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")

    provider = get_notification_provider()

    assert isinstance(provider, SmtpNotificationProvider)
