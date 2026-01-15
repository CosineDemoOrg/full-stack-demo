import logging
from typing import Protocol

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationProvider(Protocol):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None: ...


class ConsoleNotificationProvider:
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "ConsoleNotificationProvider - email:\nTo: %s\nSubject: %s\nContent: %s",
            email_to,
            subject,
            html_content,
        )


class SMTPNotificationProvider:
    def __init__(self) -> None:
        if not settings.emails_enabled:
            msg = "Email configuration is missing; cannot use SMTP notification provider"
            raise RuntimeError(msg)

    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
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
        logger.info("SMTPNotificationProvider - send email result: %s", response)


def get_notification_provider() -> NotificationProvider:
    provider_name = settings.NOTIFICATIONS_PROVIDER
    if provider_name == "console":
        return ConsoleNotificationProvider()
    return SMTPNotificationProvider()


notifications = get_notification_provider()