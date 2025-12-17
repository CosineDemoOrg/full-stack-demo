from app.notifications import (
    ConsoleEmailProvider,
    EmailMessage,
    NotificationService,
    SMTPEmailProvider,
)


class FailingProvider:
    def __init__(self) -> None:
        self.sent_messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.sent_messages.append(message)
        raise RuntimeError("fail")


def test_console_email_provider_logs(caplog):
    provider = ConsoleEmailProvider()
    message = EmailMessage(
        to="user@example.com",
        subject="Subject",
        html="<p>Body</p>",
    )

    with caplog.at_level("INFO"):
        provider.send(message)

    assert "Console email provider: email prepared" in caplog.text
    assert "user@example.com" in caplog.text


def test_smtp_email_provider_uses_emails_library(monkeypatch):
    sent: dict[str, object] = {}

    class DummyMessage:
        def __init__(self, subject: str, html: str, mail_from: tuple[str, str]):
            self.subject = subject
            self.html = html
            self.mail_from = mail_from

        def send(self, to: str, smtp: dict[str, object]):
            sent["to"] = to
            sent["smtp"] = smtp
            return "ok"

    # Patch the emails.Message class used inside the provider module.
    import app.notifications.providers as providers_module

    monkeypatch.setattr(providers_module.emails, "Message", DummyMessage)

    provider = SMTPEmailProvider(
        host="smtp.example.com",
        port=587,
        from_name="App",
        from_email="no-reply@example.com",
        user="user",
        password="pass",
        use_tls=True,
        use_ssl=False,
    )

    message = EmailMessage(
        to="user@example.com",
        subject="Subject",
        html="<p>Body</p>",
    )

    provider.send(message)

    assert sent["to"] == "user@example.com"
    smtp_options = sent["smtp"]
    assert isinstance(smtp_options, dict)
    assert smtp_options["host"] == "smtp.example.com"
    assert smtp_options["port"] == 587
    assert smtp_options["tls"] is True
    assert smtp_options["user"] == "user"
    assert smtp_options["password"] == "pass"


def test_notification_service_wraps_provider_errors():
    provider = FailingProvider()
    service = NotificationService(provider)

    try:
        # We call the internal _send to focus on error wrapping behavior.
        service._send(  # type: ignore[attr-defined]
            "test",
            EmailMessage(
                to="user@example.com",
                subject="Subject",
                html="<p>Body</p>",
            ),
        )
    except Exception as exc:  # noqa: BLE001
        # NotificationService should wrap lower-level errors.
        from app.notifications import NotificationError

        assert isinstance(exc, NotificationError)
    else:  # pragma: no cover - defensive, test should always raise
        raise AssertionError("Expected NotificationError to be raised")