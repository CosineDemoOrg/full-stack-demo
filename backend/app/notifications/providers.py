import logging
from dataclasses import dataclass
from typing import Protocol

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger("app.notifications")


@dataclass
class EmailMessage:
    email_to: str
    subject: str
    html_content: str


class NotificationError(Exception):
    """Raised when a notification cannot be sent."""


class NotificationProvider(Protocol):
    def send_email(self, message: EmailMessage) -> None:  # pragma: no cover - protocol
        ...


class ConsoleNotificationProvider:
    """Notification provider that logs emails instead of sending them."""

    provider_name = "console"

    def send_email(self, message: EmailMessage) -> None:
        log_data = {
            "event": "notification.send",
            "provider": self.provider_name,
            "to": message.email_to,
            "subject": message.subject,
        }
        logger.info(log_data)


class SMTPNotificationProvider:
    """Notification provider that sends emails using SMTP settings."""

    provider_name = "smtp"

    def send_email(self, message: EmailMessage) -> None:
        if not settings.emails_enabled:
            error_message = "Email sending is not enabled. Check SMTP_* and EMAILS_FROM_EMAIL settings."
            logger.error(
                {
                    "event": "notification.send_failed",
                    "provider": self.provider_name,
                    "reason": "emails_not_enabled",
                    "to": message.email_to,
                    "subject": message.subject,
                }
            )
            raise NotificationError(error_message)

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

        try:
            email_message = emails.Message(
                subject=message.subject,
                html=message.html_content,
                mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
            )
            response = email_message.send(to=message.email_to, smtp=smtp_options)
            logger.info(
                {
                    "event": "notification.send",
                    "provider": self.provider_name,
                    "to": message.email_to,
                    "subject": message.subject,
                    "smtp_host": settings.SMTP_HOST,
                    "response": str(response),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                {
                    "event": "notification.send_failed",
                    "provider": self.provider_name,
                    "to": message.email_to,
                    "subject": message.subject,
                }
            )
            raise NotificationError("Failed to send email") from exc


def get_notification_provider() -> NotificationProvider:
    """Factory that returns the active notification provider based on settings."""
    provider_name = getattr(settings, "NOTIFICATION_PROVIDER", "console")
    if provider_name == "smtp":
        return SMTPNotificationProvider()
    return ConsoleNotificationProvider()