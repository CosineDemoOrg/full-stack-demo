import logging
from typing import Any

import pytest

from app.notifications import ConsoleEmailProvider, SmtpEmailProvider


def test_console_provider_logs_email(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleEmailProvider()
    with caplog.at_level(logging.INFO):
        provider.send_email(email_to="user@example.com", subject="Subject", html_content="<p>Hi</p>")
    records = [record for record in caplog.records if record.getMessage() == "Email sent"]
    assert records
    record = records[0]
    assert record.email_to == "user@example.com"
    assert record.provider == "console"


def test_smtp_provider_handles_disabled_emails(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    # When emails are disabled, the provider should log a warning and not attempt to send.
    from app.core.config import settings

    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", None)

    # Patch emails.Message to ensure it is not called
    class DummyMessage:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
            raise AssertionError("Message should not be instantiated when emails are disabled")

    monkeypatch.setattr("app.notifications.providers.emails.Message", DummyMessage, raising=False)

    provider = SmtpEmailProvider()
    with caplog.at_level(logging.WARNING):
        provider.send_email(email_to="user@example.com", subject="Subject", html_content="<p>Hi</p>")

    records = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert any("Tried to send email but emails are disabled" in r.getMessage() for r in records)