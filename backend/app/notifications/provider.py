from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger("app.notifications")


@dataclass
class EmailMessage:
    email_to: str
    subject: str
    html_content: str


class NotificationError(Exception):
    """Raised when a notification provider fails to send a message."""

    def __init__(self, *, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(message)


class NotificationProvider(Protocol):
    def send_email(self, message: EmailMessage) -> None:  # pragma: no cover - protocol
        ...


class ConsoleNotificationProvider:
    """Notification provider that logs the email instead of sending it."""

    provider_name = "console"

    def send_email(self, message: EmailMessage) -> None:
        logger.info(
            "Sending email (console provider)",
            extra={
                "event": "notification.send",
                "provider": self.provider_name,
                "to": message.email_to,
                "subject": message.subject,
            },
        )
        logger.debug(
            "Email content",
            extra={
                "event": "notification.payload",
                "provider": self.provider_name,
                "to": message.email_to,
                "subject": message.subject,
                "html_length": len(message.html_content),
            },
        )


class SMTPNotificationProvider:
    """Notification provider that sends emails via SMTP using the 'emails' package."""

    provider_name = "smtp"

    def send_email(self, message: EmailMessage) -> None:
        # Import lazily so tests can monkeypatch easily and to avoid import cycles
        import emails  # type: ignore

        if not settings.emails_enabled:
            logger.info(
                "Emails are disabled by configuration, skipping SMTP send",
                extra={
                    "event": "notification.skipped",
                    "provider": self.provider_name,
                    "to": message.email_to,
                    "subject": message.subject,
                },
            )
            return

        try:
            email_message = emails.Message(
                subject=message.subject,
                html=message.html_content,
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

            logger.info(
                "Sending email via SMTP provider",
                extra={
                    "event": "notification.send",
                    "provider": self.provider_name,
                    "to": message.email_to,
                    "subject": message.subject,
                    "host": settings.SMTP_HOST,
                    "port": settings.SMTP_PORT,
                },
            )
            response = email_message.send(to=message.email_to, smtp=smtp_options)
            logger.info(
                "Email sent via SMTP provider",
                extra={
                    "event": "notification.sent",
                    "provider": self.provider_name,
                    "to": message.email_to,
                    "subject": message.subject,
                    "response": str(response),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Failed to send email via SMTP provider",
                extra={
                    "event": "notification.error",
                    "provider": self.provider_name,
                    "to": message.email_to,
                    "subject": message.subject,
                },
            )
            raise NotificationError(
                provider=self.provider_name,
                message="Failed to send email via SMTP provider",
            ) from exc