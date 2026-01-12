from __future__ import annotations

from typing import Any

import pytest

from app.core.config import settings
from app.notifications.providers import EmailMessage, get_notification_provider
from app.notifications.providers.console import ConsoleNotificationProvider
from app.notifications.providers.smtp import SMTPNotificationProvider


def test_get_notification_provider_console(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console")
    provider = get_notification_provider()
    assert isinstance(provider, ConsoleNotificationProvider)


def test_get_notification_provider_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")
    provider = get_notification_provider()
    assert isinstance(provider, SMTPNotificationProvider)


def test_smtp_provider_builds_smtp_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(settings, "SMTP_TLS", True)
    monkeypatch.setattr(settings, "SMTP_SSL", False)
    monkeypatch.setattr(settings, "SMTP_USER", "user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pass")
    provider = get_notification_provider()
    assert isinstance(provider, SMTPNotificationProvider)

    smtp_options = provider._build_smtp_options()  # type: ignore[attr-defined]
    assert smtp_options["host"] == "smtp.example.com"
    assert smtp_options["port"] == 2525
    assert smtp_options["tls"] is True
    assert "ssl" not in smtp_options
    assert smtp_options["user"] == "user"
    assert smtp_options["password"] == "pass"


def test_smtp_provider_send_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "info@example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_NAME", "Example")
    monkeypatch.setattr(settings, "SMTP_PORT", 2525)
    monkeypatch.setattr(settings, "SMTP_TLS", True)
    monkeypatch.setattr(settings, "SMTP_SSL", False)

    sent_messages: list[dict[str, Any]] = []

    class DummyEmailMessage:
        def __init__(self, subject: str, html: str, mail_from: tuple[str, str]) -> None:
            self.subject = subject
            self.html = html
            self.mail_from = mail_from

        def send(self, to: str, smtp: dict[str, Any]) -> str:
            sent_messages.append(
                {
                    "to": to,
                    "smtp": smtp,
                    "subject": self.subject,
                    "html": self.html,
                    "mail_from": self.mail_from,
                }
            )
            return "ok"

    import app.notifications.providers.smtp as smtp_module

    monkeypatch.setattr(smtp_module, "emails", type("EmailsModule", (), {"Message": DummyEmailMessage}))

    provider = get_notification_provider()
    assert isinstance(provider, SMTPNotificationProvider)

    message = EmailMessage(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Hello</p>",
    )
    provider.send_email(message)

    assert len(sent_messages) == 1
    sent = sent_messages[0]
    assert sent["to"] == "user@example.com"
    assert sent["subject"] == "Subject"
    assert sent["html"] == "<p>Hello</p>"