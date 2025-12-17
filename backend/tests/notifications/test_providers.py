from app.notifications.models import EmailData
from app.notifications.providers import ConsoleEmailProvider, SMTPEmailProvider


class DummyMessage:
    def __init__(self) -> None:
        self.sent_args: dict | None = None

    def send(self, to: str, smtp: dict) -> str:  # type: ignore[override]
        self.sent_args = {"to": to, "smtp": smtp}
        return "ok"


def test_console_email_provider_does_not_raise(capsys) -> None:
    provider = ConsoleEmailProvider()
    email = EmailData(email_to="user@example.com", subject="Test", html_content="<p>Hi</p>")

    provider.send_email(email)

    captured = capsys.readouterr()
    assert "user@example.com" in captured.out
    assert "Test" in captured.out


def test_smtp_email_provider_builds_smtp_options(monkeypatch) -> None:
    dummy = DummyMessage()

    def dummy_message(*args, **kwargs):  # noqa: ANN001, ANN003
        return dummy

    import app.notifications.providers as providers_module

    monkeypatch.setattr(providers_module, "emails", type("E", (), {"Message": dummy_message}))  # type: ignore[attr-defined]

    provider = SMTPEmailProvider()
    email = EmailData(email_to="user@example.com", subject="Test", html_content="<p>Hi</p>")

    provider.send_email(email)

    assert dummy.sent_args is not None
    assert dummy.sent_args["to"] == "user@example.com"
    assert "host" in dummy.sent_args["smtp"]
    assert "port" in dummy.sent_args["smtp"]