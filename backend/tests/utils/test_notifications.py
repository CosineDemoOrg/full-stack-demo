from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    SMTPNotificationProvider,
    get_notification_provider,
)


def test_console_notification_provider_logs(caplog) -> None:
    provider = ConsoleNotificationProvider()
    with caplog.at_level("INFO"):
        provider.send_email(
            email_to="user@example.com",
            subject="Test",
            html_content="<p>Hello</p>",
        )
    # Ensure that something was logged with the expected pieces of data.
    joined = "\n".join(caplog.messages)
    assert "Console notification email" in joined
    assert "user@example.com" in joined
    assert "Test" in joined
    assert "Hello" in joined


def test_smtp_notification_provider_uses_emails_library(monkeypatch) -> None:
    sent_args: dict[str, object] = {}

    class DummyMessage:
        def __init__(self, subject: str, html: str, mail_from: tuple[str, str | None]):
            self.subject = subject
            self.html = html
            self.mail_from = mail_from

        def send(self, to: str, smtp: dict[str, object]) -> str:
            sent_args["to"] = to
            sent_args["smtp"] = smtp
            sent_args["subject"] = self.subject
            sent_args["html"] = self.html
            return "ok"

    dummy_emails = MagicMock()
    dummy_emails.Message = DummyMessage  # type: ignore[attr-defined]

    monkeypatch.setattr("app.notifications.emails", dummy_emails, raising=False)

    # Ensure settings are populated for the SMTP provider.
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_PORT", 587),
        patch("app.core.config.settings.SMTP_TLS", True),
        patch("app.core.config.settings.SMTP_SSL", False),
        patch("app.core.config.settings.SMTP_USER", "user"),
        patch("app.core.config.settings.SMTP_PASSWORD", "pass"),
        patch("app.core.config.settings.EMAILS_FROM_EMAIL", "noreply@example.com"),
        patch("app.core.config.settings.EMAILS_FROM_NAME", "Example App"),
    ):
        provider = SMTPNotificationProvider()
        provider.send_email(
            email_to="dest@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )

    assert sent_args["to"] == "dest@example.com"
    smtp = sent_args["smtp"]
    assert isinstance(smtp, dict)
    assert smtp["host"] == "smtp.example.com"
    assert smtp["port"] == 587
    assert smtp["tls"] is True
    assert smtp["user"] == "user"
    assert smtp["password"] == "pass"
    assert sent_args["subject"] == "Subject"
    assert sent_args["html"] == "<p>Body</p>"


def test_get_notification_provider_uses_env(monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.NOTIFICATIONS_PROVIDER", "console")
    provider = get_notification_provider()
    assert isinstance(provider, ConsoleNotificationProvider)

    # Clear the cache and switch provider.
    get_notification_provider.cache_clear()  # type: ignore[attr-defined]

    monkeypatch.setattr("app.core.config.settings.NOTIFICATIONS_PROVIDER", "smtp")
    provider = get_notification_provider()
    from app.notifications import SMTPNotificationProvider as SMTPProviderCls

    assert isinstance(provider, SMTPProviderCls)