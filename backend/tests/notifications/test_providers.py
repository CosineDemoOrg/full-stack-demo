import types

import pytest

from app.notifications.providers.base import EmailMessage
from app.notifications.providers.console import ConsoleProvider
from app.notifications.providers.smtp import SmtpProvider
from app.core.config import settings


def test_console_provider_logs(caplog):
    provider = ConsoleProvider()
    with caplog.at_level("INFO"):
        provider.send(EmailMessage(to="a@b.com", subject="Subj", html="<p>Hi</p>"))
    # Ensure something was logged
    assert any("email_send" in rec.message for rec in caplog.records)


def test_smtp_provider_builds_and_sends(monkeypatch):
    # Ensure SMTP configured for this test
    settings.SMTP_HOST = "localhost"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"

    sent = {}

    class DummyResponse:
        def __repr__(self) -> str:
            return "dummy"

    class DummyMessage:
        def __init__(self, subject, html, mail_from):
            sent["subject"] = subject
            sent["html"] = html
            sent["mail_from"] = mail_from

        def send(self, to, smtp):
            sent["to"] = to
            sent["smtp"] = smtp
            return DummyResponse()

    # Patch emails.Message to our dummy
    import app.notifications.providers.smtp as smtp_mod

    monkeypatch.setattr(smtp_mod, "emails", types.SimpleNamespace(Message=DummyMessage))

    provider = SmtpProvider()
    provider.send(EmailMessage(to="user@example.com", subject="Hello", html="<p>Test</p>"))

    assert sent["to"] == "user@example.com"
    assert sent["subject"] == "Hello"
    assert "host" in sent["smtp"]