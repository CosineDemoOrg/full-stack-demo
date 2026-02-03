from __future__ import annotations

from typing import Any

import logging
from _pytest.logging import LogCaptureFixture
from emails import Message  # type: ignore

from app.core.config import settings
from app.notifications import (
    ConsoleNotificationProvider,
    SMTPNotificationProvider,
    get_notification_provider,
)


class DummyResponse:
    def __repr__(self) -> str:  # pragma: no cover - repr not used in assertions
        return "dummy-response"


def test_console_notification_provider_logs(caplog: LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider()

    with caplog.at_level(logging.INFO):
        provider.send_email(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )

    assert any(
        "ConsoleNotificationProvider" in message and "user@example.com" in message
        for message in caplog.messages
    )


def test_smtp_notification_provider_sends_email(monkeypatch: Any) -> None:
    sent_args: dict[str, Any] = {}

    def fake_send(self: Message, to: str, smtp: dict[str, Any]) -> DummyResponse:  # type: ignore[override]
        sent_args["to"] = to
        sent_args["smtp"] = smtp
        sent_args["subject"] = self.subject
        sent_args["html"] = self.html
        return DummyResponse()

    monkeypatch.setattr(Message, "send", fake_send, raising=False)

    # Ensure settings allow emails
    settings.SMTP_HOST = "smtp.example.com"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"  # type: ignore[assignment]

    provider = SMTPNotificationProvider()
    provider.send_email(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    assert sent_args["to"] == "user@example.com"
    assert sent_args["smtp"]["host"] == "smtp.example.com"
    assert sent_args["subject"] == "Subject"
    assert sent_args["html"] == "<p>Body</p>"


def test_get_notification_provider_uses_setting(monkeypatch: Any) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console", raising=False)
    provider = get_notification_provider()
    assert isinstance(provider, ConsoleNotificationProvider)

    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp", raising=False)
    provider = get_notification_provider()
    assert isinstance(provider, SMTPNotificationProvider)
