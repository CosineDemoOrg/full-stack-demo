from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings


@dataclass
class EmailMessage:
    to: str
    subject: str
    html_content: str


class NotificationProvider(Protocol):
    def send_email(self, message: EmailMessage) -> None:  # pragma: no cover - interface
        ...


def get_provider() -> NotificationProvider:
    """
    Factory that returns the configured notifications provider.
    Defaults to Console provider. Uses SMTP when selected and configured.
    """
    if settings.NOTIFICATIONS_PROVIDER == "smtp" and settings.emails_enabled:
        from .providers.smtp import SMTPProvider

        return SMTPProvider()
    else:
        from .providers.console import ConsoleProvider

        return ConsoleProvider()