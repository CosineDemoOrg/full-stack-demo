import types

import pytest

from app.notifications.providers.console import ConsoleProvider
from app.notifications.providers.smtp import SmtpProvider
from app.core.config import settings


def test_console_provider_does_not_raise():
    provider = ConsoleProvider()
    provider.send(email_to="user@example.com", subject="Hello", html_content="<p>Test</p>")


class DummyMessage:
    def __init__(self, subject: str, html: str, mail_from: tuple[str | None, str | None]):
        self.subject = subject
        self.html = html
        self.mail_from = mail_from
        self.sent_with: dict | None = None

    def send(self, to: str, smtp: dict) -> str:
        self.sent_with = {"to": to, "smtp": smtp}
        return "ok"


def test_smtp_provider_builds_options(monkeypatch):
    # Ensure settings allow smtp
    settings.SMTP_HOST = "smtp.example.com"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"

    # Patch emails.Message to our dummy
    import emails as emails_mod  # type: ignore

    monkeypatch.setattr(emails_mod, "Message", DummyMessage)

    provider = SmtpProvider()
    provider.send(email_to="user@example.com", subject="Subj", html_content="<p>Body</p>")