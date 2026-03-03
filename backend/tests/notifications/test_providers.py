from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.notifications.provider import (
    ConsoleEmailProvider,
    EmailMessage,
    NotificationError,
    SmtpEmailProvider,
)


def test_console_provider_does_not_raise():
    provider = ConsoleEmailProvider()
    # Should just log, not raise
    provider.send(EmailMessage(to="user@example.com", subject="Hello", html="<p>Hi</p>"))


def test_smtp_provider_missing_config_raises(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", None)
    provider = SmtpEmailProvider()
    with pytest.raises(NotificationError):
        provider.send(EmailMessage(to="user@example.com", subject="Hello", html="<p>Hi</p>"))


def test_smtp_provider_sends(monkeypatch):
    # Provide minimal SMTP settings
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_TLS", True)
    monkeypatch.setattr(settings, "SMTP_SSL", False)
    monkeypatch.setattr(settings, "SMTP_USER", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_NAME", "Test")

    sent = {}

    class DummyResponse:
        def __str__(self) -> str:
            return "ok"

    class DummyMessage:
        def __init__(self, subject, html, mail_from):
            sent["subject"] = subject
            sent["html"] = html
            sent["mail_from"] = mail_from

        def send(self, to, smtp):
            sent["to"] = to
            sent["smtp"] = smtp
            return DummyResponse()

    # Patch emails.Message
    import app.notifications.provider as provider_mod

    monkeypatch.setattr(provider_mod, "emails", SimpleNamespace(Message=DummyMessage))

    provider = SmtpEmailProvider()
    provider.send(EmailMessage(to="user@example.com", subject="Hello", html="<p>Hi</p>"))

    assert sent["to"] == "user@example.com"
    assert sent["subject"] == "Hello"
    assert sent["mail_from"][1] == "noreply@example.com"
    assert "host" in sent["smtp"]