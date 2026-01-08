import logging
from typing import Protocol

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationProvider(Protocol):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover - protocol
        ...


class ConsoleNotificationProvider:
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "Console notification email\nTo: %s\nSubject: %s\nBody (truncated): %s",
            email_to,
            subject,
            html_content[:200],
        )


class SmtpNotificationProvider:
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
        logger.info("SMTP notification email result: %s", response)


def _get_provider() -> NotificationProvider:
    if settings.NOTIFICATIONS_PROVIDER == "console":
        return ConsoleNotificationProvider()
    return SmtpNotificationProvider()


provider: NotificationProvider = _get_provider()


def send_notification_email(*, email_to: str, subject: str, html_content: str) -> None:
    provider.send_email(email_to=email_to, subject=subject, html_content=html_content)