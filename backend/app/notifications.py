import logging
from abc import ABC, abstractmethod

from emails import Message  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    @abstractmethod
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleNotificationProvider(NotificationProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "ConsoleNotificationProvider: email_to=%s subject=%s html_length=%d",
            email_to,
            subject,
            len(html_content),
        )


class SMTPNotificationProvider(NotificationProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        if not settings.emails_enabled:
            raise AssertionError("no provided configuration for email variables")

        message = Message(
            subject=subject,
            html=html_content,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options: dict[str, object] = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
        }
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD
        response = message.send(to=email_to, smtp=smtp_options)
        logger.info("SMTPNotificationProvider send email result: %s", response)


def get_notification_provider() -> NotificationProvider:
    provider_name = settings.NOTIFICATIONS_PROVIDER
    if provider_name == "console":
        return ConsoleNotificationProvider()
    if provider_name == "smtp":
        return SMTPNotificationProvider()
    raise ValueError(f"Unknown notifications provider: {provider_name}")
