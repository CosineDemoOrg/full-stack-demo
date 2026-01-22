from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.notifications import send_email_notification


class DummyMessage:
    def __init__(self, subject: str, html: str, mail_from: tuple[str | None, str | None]):
        self.subject = subject
        self.html = html
        self.mail_from = mail_from
        self.sent_with: dict[str, Any] | None = None

    def send(self, to: str, smtp: dict[str, Any]) -> str:
        self.sent_with = {"to": to, "smtp": smtp}
        return "ok"


def test_console_provider_uses_logging(caplog) -> None:
    settings.NOTIFICATIONS_PROVIDER = "console"  # type: ignore[attr-defined]

    caplog.set_level("INFO")
    send_email_notification(email_to="user@example.com", subject="Subj", html_content="<p>Body</p>")

    messages = [record.getMessage() for record in caplog.records]
    assert any("Console email to user@example.com" in message for message in messages)


def test_smtp_provider_sends_via_emails(monkeypatch) -> None:
    settings.NOTIFICATIONS_PROVIDER = "smtp"  # type: ignore[attr-defined]
    settings.SMTP_HOST = "smtp.example.com"
    settings.SMTP_PORT = 25
    settings.EMAILS_FROM_EMAIL = "from@example.com"  # type: ignore[assignment]
    settings.EMAILS_FROM_NAME = "From Name"  # type: ignore[assignment]

    from app import notifications as notifications_module

    sent: dict[str, Any] = {}

    def dummy_message_factory(subject: str, html: str, mail_from: tuple[str | None, str | None]) -> DummyMessage:  # type: ignore[type-arg]
        msg = DummyMessage(subject=subject, html=html, mail_from=mail_from)
        sent["msg"] = msg
        return msg

    monkeypatch.setattr(notifications_module.emails, "Message", dummy_message_factory)

    send_email_notification(
        email_to="user@example.com",
        subject="Subject",
        html_content="<p>Body</p>",
    )

    assert "msg" in sent
    msg = sent["msg"]
    assert isinstance(msg, DummyMessage)
    assert msg.subject == "Subject"
    assert msg.mail_from == ("From Name", "from@example.com")
    assert msg.sent_with is not None
    assert msg.sent_with["to"] == "user@example.com"
    assert msg.sent_with["smtp"]["host"] == "smtp.example.com"