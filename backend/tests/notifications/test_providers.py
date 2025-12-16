from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.notifications.provider import (
    ConsoleNotificationProvider,
    EmailMessage,
    NotificationError,
    SMTPNotificationProvider,
)


def test_console_provider_logs_email(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider()
    message = EmailMessage(
        email_to="user@example.com",
        subject="Test Subject",
        html_content="<p>Hello</p>",
    )

    with caplog.at_level("INFO"):
        provider.send_email(message)

    assert any("Sending email (console provider)" in record.getMessage() for record in caplog.records)


def test_smtp_provider_sends_email(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_send = MagicMock()

    class FakeEmailsMessage:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401
            """Fake init."""

        def send(self, to: str, smtp: dict[str, object]) -> object:  # noqa: ARG002
            return fake_send(to=to, smtp=smtp)

    monkeypatch.setattr("app.notifications.provider.emails.Message", FakeEmailsMessage)

    provider = SMTPNotificationProvider()
    message = EmailMessage(
        email_to="user@example.com",
        subject="Test Subject",
        html_content="<p>Hello</p>",
    )

    provider.send_email(message)

    fake_send.assert_called_once()
    kwargs = fake_send.call_args.kwargs
    assert kwargs["to"] == "user@example.com"
    assert isinstance(kwargs["smtp"], dict)


def test_smtp_provider_wraps_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingEmailsMessage:
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401
            """Fake init."""

        def send(self, to: str, smtp: dict[str, object]) -> object:  # noqa: ARG002
            raise RuntimeError("SMTP failure")

    monkeypatch.setattr(
        "app.notifications.provider.emails.Message", FailingEmailsMessage
    )

    provider = SMTPNotificationProvider()
    message = EmailMessage(
        email_to="user@example.com",
        subject="Test Subject",
        html_content="<p>Hello</p>",
    )

    with pytest.raises(NotificationError):
        provider.send_email(message)