import logging
from abc import ABC, abstractmethod
from typing import Any

import emails  # type: ignore

from app.core.config import settings
from app.notifications.models import EmailData

logger = logging.getLogger("app.notifications")


class NotificationError(Exception):
    """Raised when sending a notification fails."""


class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, email: EmailData) -> None:
        """Send a single email message."""


class ConsoleEmailProvider(EmailProvider):
    def send_email(self, email: EmailData) -> None:
        logger.info(
            "Sending email via console provider",
            extra={
                "provider": "console",
                "email_to": email.email_to,
                "subject": email.subject,
            },
        )
        print(f"[EMAIL] To: {email.email_to} | Subject: {email.subject}")
        print(email.html_content)


class SMTPEmailProvider(EmailProvider):
    def send_email(self, email: EmailData) -> None:
        if not settings.emails_enabled:
            logger.warning(
                "SMTP email sending is disabled by configuration",
                extra={
                    "provider": "smtp",
                    "email_to": email.email_to,
                    "subject": email.subject,
                },
            )
            return

        message = emails.Message(
            subject=email.subject,
            html=email.html_content,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options: dict[str, Any] = {
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
            response = message.send(to=email.email_to, smtp=smtp_options)
            logger.info(
                "Email sent",
                extra={
                    "provider": "smtp",
                    "email_to": email.email_to,
                    "subject": email.subject,
                    "response": str(response),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Error sending email",
                extra={
                    "provider": "smtp",
                    "email_to": email.email_to,
                    "subject": email.subject,
                },
            )
            raise NotificationError("Error sending email") from exc


def get_email_provider() -> EmailProvider:
    provider = settings.NOTIFICATIONS_PROVIDER
    if provider == "console":
        return ConsoleEmailProvider()
    if provider == "smtp":
        return SMTPEmailProvider()
    raise ValueError(f"Unsupported notifications provider: {provider}")