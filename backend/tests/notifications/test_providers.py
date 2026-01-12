import logging

import pytest

from app.notifications.models import EmailMessage
from app.notifications.providers import ConsoleEmailProvider, SmtpEmailProvider


def test_console_provider_logs_and_prints(caplog, capsys):
    provider = ConsoleEmailProvider()
    message = EmailMessage(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    with caplog.at_level(logging.INFO):
        provider.send(message)

    assert any(
        "Sending email via console provider" in record.getMessage()
        for record in caplog.records
    )

    captured = capsys.readouterr()
    assert "user@example.com" in captured.out
    assert "Subject" in captured.out
    assert "Body" in captured.out


def test_smtp_provider_builds_message_and_logs(monkeypatch, caplog):
    sent_messages: list[dict] = []

    class DummyResponse:
        def __str__(self) -> str:  # pragma: no cover - trivial
            return "OK"

    class DummyEmailsMessage:
        def __init__(self, subject: str, html: str, mail_from: tuple[str, str | None]):
            self.subject = subject
            self.html = html
            self.mail_from = mail_from

        def send(self, to: str, smtp: dict) -> DummyResponse:
            sent_messages.append(
                {
                    "to": to,
                    "subject": self.subject,
                    "html": self.html,
                    "mail_from": self.mail_from,
                    "smtp": smtp,
                }
            )
            return DummyResponse()

    monkeypatch.setattr("app.notifications.providers.emails.Message", DummyEmailsMessage)

    from app.core.config import settings

    settings.SMTP_HOST = "smtp.example.com"
    settings.SMTP_PORT = 587
    settings.SMTP_TLS = True
    settings.SMTP_SSL = False
    settings.SMTP_USER = "user"
    settings.SMTP_PASSWORD = "pass"
    settings.EMAILS_FROM_NAME = "Project"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"

    provider = SmtpEmailProvider()
    message = EmailMessage(
        email_to="dest@example.com",
        subject="Hi",
        html_content="<p>Hi</p>",
    )

    with caplog.at_level(logging.INFO):
        provider.send(message)

    assert sent_messages
    sent = sent_messages[0]
    assert sent["to"] == "dest@example.com"
    assert sent["subject"] == "Hi"
    assert sent["html"] == "<p>Hi</p>"
    assert sent["smtp"]["host"] == "smtp.example.com"
    assert sent["smtp"]["port"] == 587
    assert sent["smtp"]["tls"] is True

    assert any(
        "Sending email via SMTP provider" in record.getMessage()
        for record in caplog.records
    )
    assert any(
        "Email send completed" in record.getMessage() for record in caplog.records
    )