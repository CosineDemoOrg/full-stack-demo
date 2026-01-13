import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings
from app.utils import EmailData, send_email

logger = logging.getLogger(__name__)


@dataclass
class Notification:
    email_to: str
    subject: str
    html_content: str


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, notification: Notification) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleNotificationProvider(NotificationProvider):
    def send(self, notification: Notification) -> None:
        logger.info(
            "ConsoleNotificationProvider send: to=%s subject=%s",
            notification.email_to,
            notification.subject,
        )


class SMTPNotificationProvider(NotificationProvider):
    def send(self, notification: Notification) -> None:
        email_data = EmailData(
            html_content=notification.html_content,
            subject=notification.subject,
        )
        # Reuse existing SMTP email sending logic
        send_email(
            email_to=notification.email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )


def get_notification_provider() -> NotificationProvider:
    provider_name = settings.NOTIFICATIONS_PROVIDER.lower()
    if provider_name == "console":
        return ConsoleNotificationProvider()
    if provider_name == "smtp":
        return SMTPNotificationProvider()
    logger.warning(
        "Unknown NOTIFICATIONS_PROVIDER=%s, falling back to SMTPNotificationProvider",
        provider_name,
    )
    return SMTPNotificationProvider()