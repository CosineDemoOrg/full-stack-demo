import logging
from abc import ABC, abstractmethod

import emails  # type: ignore

from app.core.config import settings


logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    @abstractmethod
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        """Send an email notification."""


class ConsoleNotificationProvider(NotificationProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "Console notification provider sending email",
            extra={
                "email_to": email_to,
                "subject": subject,
                "html_length": len(html_content),
            },
        )


class SMTPNotificationProvider(NotificationProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        assert settings.emails_enabled, "no provided configuration for email variables"
        message = emails.Message(
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
        logger.info("send email result: %s", response)


def get_notification_provider() -> NotificationProvider:
    provider_name = getattr(settings, "NOTIFICATIONS_PROVIDER", "smtp")
    normalized = provider_name.lower()
    if normalized == "console":
        return ConsoleNotificationProvider()
    if normalized == "smtp":
        return SMTPNotificationProvider()
    raise ValueError(f"Unknown NOTIFICATIONS_PROVIDER: {provider_name}")


notification_provider: NotificationProvider = get_notification_provider()
