from app.notifications.provider import ConsoleEmailProvider
from app.notifications.service import NotificationsService


def test_console_provider_send_does_not_raise() -> None:
    provider = ConsoleEmailProvider()
    provider.send(email_to="test@example.com", subject="Subj", html_content="<p>Hi</p>")


def test_notifications_service_uses_provider() -> None:
    calls: dict[str, int] = {"count": 0}

    class DummyProvider(ConsoleEmailProvider):
        def send(self, *, email_to: str, subject: str, html_content: str) -> None:
            calls["count"] += 1

    service = NotificationsService(provider=DummyProvider())
    service.send_test_email(email_to="test@example.com")
    assert calls["count"] == 1