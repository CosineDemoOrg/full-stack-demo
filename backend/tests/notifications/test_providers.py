import builtins
from types import SimpleNamespace

import pytest

from app.notifications.provider import EmailMessage, get_provider
from app.core.config import settings


def test_console_provider_sends_and_logs(monkeypatch):
    # Force console provider
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console")

    provider = get_provider()
    message = EmailMessage(to="user@example.com", subject="Test", html_content="<p>hi</p>")

    # Capture print
    printed = {}

    def fake_print(*args, **kwargs):
        printed["args"] = args
        printed["kwargs"] = kwargs

    monkeypatch.setattr(builtins, "print", fake_print)

    provider.send_email(message)

    assert "ConsoleProvider" in printed["args"][0]
    assert "user@example.com" in printed["args"][0]
    assert "Test" in printed["args"][0]


def test_smtp_provider_builds_and_calls_send(monkeypatch):
    # Force smtp provider and configure minimal settings
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "localhost")
    monkeypatch.setattr(settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "info@example.com")

    # Mock emails.Message.send
    sent = {}

    class FakeMessage:
        def __init__(self, subject=None, html=None, mail_from=None):
            sent["subject"] = subject
            sent["html"] = html
            sent["mail_from"] = mail_from

        def send(self, to=None, smtp=None):
            sent["to"] = to
            sent["smtp"] = smtp
            return SimpleNamespace(status_code=250)

    import app.notifications.providers.smtp as smtp_mod

    monkeypatch.setattr(smtp_mod, "emails", SimpleNamespace(Message=FakeMessage))

    provider = get_provider()
    msg = EmailMessage(to="user@example.com", subject="Hello", html_content="<p>hello</p>")
    provider.send_email(msg)

    assert sent["to"] == "user@example.com"
    assert sent["subject"] == "Hello"
    assert sent["mail_from"][1] == settings.EMAILS_FROM_EMAIL
    assert sent["smtp"]["host"] == settings.SMTP_HOST
    assert sent["smtp"]["port"] == settings.SMTP_PORT