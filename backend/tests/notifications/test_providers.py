import logging
from typing import Any

import pytest

from app.core.config import settings
from app.notifications import get_provider
from app.notifications.providers.console import ConsoleProvider
from app.notifications.providers.smtp import SMTPProvider


def test_get_provider_console(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "console")
    provider = get_provider()
    assert isinstance(provider, ConsoleProvider)


def test_get_provider_smtp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")
    provider = get_provider()
    assert isinstance(provider, SMTPProvider)


def test_console_provider_logs(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleProvider()
    with caplog.at_level(logging.INFO):
        result = provider.send(email_to="user@example.com", subject="Subj", html_content="<p>Hi</p>")
    assert result == {"status": "logged"}
    assert any("console_notification" in rec.message for rec in caplog.records)


def test_smtp_provider_sends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setattr(settings, "EMAILS_FROM_NAME", "Example")
    monkeypatch.setattr(settings, "SMTP_TLS", True)
    sent_calls: dict[str, Any] = {}

    class DummyMessage:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

        def send(self, to: str, smtp: dict[str, Any]) -> dict[str, Any]:
            sent_calls["to"] = to
            sent_calls["smtp"] = smtp
            return {"status": "ok"}

    import app.notifications.providers.smtp as smtp_mod

    monkeypatch.setattr(smtp_mod, "emails", pytest.Namespace(Message=DummyMessage))

    provider = SMTPProvider()
    result = provider.send(email_to="user@example.com", subject="Subj", html_content="<p>Hi</p>")
    assert result == {"status": "ok"}
    assert sent_calls["to"] == "user@example.com"
    assert sent_calls["smtp"]["host"] == "smtp.example.com"