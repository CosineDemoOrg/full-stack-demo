from typing import Any

from app.core.config import settings
from app.notifications.email import (
    ConsoleEmailProvider,
    SmtpEmailProvider,
    get_email_provider,
)


def test_console_email_provider_logs(caplog: Any) -> None:
    provider = ConsoleEmailProvider()
    with caplog.at_level("INFO"):
        provider.send(email_to="user@example.com", subject="Test", html_content="<p>Hi</p>")

    assert any("email.sent" in record.message for record in caplog.records)


def test_smtp_email_provider_uses_emails_message(monkeypatch: Any, caplog: Any) -> None:
    class DummyMessage:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs
            self.sent_with: dict[str, Any] | None = None

        def send(self, to: str, smtp: dict[str, Any]) -> str:
            self.sent_with = {"to": to, "smtp": smtp}
            return "ok"

    created_message: DummyMessage | None = None

    def dummy_message_factory(*args: Any, **kwargs: Any) -> DummyMessage:
        nonlocal created_message
        created_message = DummyMessage(*args, **kwargs)
        return created_message

    monkeypatch.setattr("app.notifications.email.emails.Message", dummy_message_factory)

    # Ensure emails are enabled
    settings.SMTP_HOST = "smtp.example.com"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"

    provider = SmtpEmailProvider()
    with caplog.at_level("INFO"):
        provider.send(
            email_to="user@example.com",
            subject="Subject",
            html_content="<p>Body</p>",
        )

    assert created_message is not None
    assert created_message.sent_with is not None
    assert created_message.sent_with["to"] == "user@example.com"
    assert created_message.sent_with["smtp"]["host"] == "smtp.example.com"

    assert any(
        "email.sent" in record.message and record.levelname == "INFO"
        for record in caplog.records
    )


def test_get_email_provider_console(monkeypatch: Any) -> None:
    monkeypatch.setattr("app.core.config.settings.NOTIFICATIONS_EMAIL_PROVIDER", "console")
    provider = get_email_provider()
    assert isinstance(provider, ConsoleEmailProvider)