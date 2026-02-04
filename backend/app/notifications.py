import logging
from dataclasses import dataclass
from typing import Protocol

import emails  # type: ignore

from app.core.config import settings


logger = logging.getLogger(__name__)


class NotificationProvider(Protocol):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover - interface only
        ...


@dataclass
class ConsoleNotificationProvider:
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "Console email notification: to=%s subject=%s html_length=%d",
            email_to,
            subject,
            len(html_content),
        )


class SmtpNotificationProvider:
    def __init__(self) -> None:
        self._emails = emails

    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        assert settings.emails_enabled, "no provided configuration for email variables"

        message = self._emails.Message(
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
    provider_name = settings.NOTIFICATIONS_PROVIDER.lower()

    if provider_name == "console":
        return ConsoleNotificationProvider()
    if provider_name == "smtp":
        return SmtpNotificationProvider()

    # Fallback to SMTP to preserve existing behavior if an unknown value is provided.
    logger.warning(
        "Unknown NOTIFICATIONS_PROVIDER=%s, falling back to 'smtp'", provider_name
    )
    return SmtpNotificationProvider()
