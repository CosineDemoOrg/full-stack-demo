from __future__ import annotations

import logging
from typing import Any

import emails  # type: ignore

from app.core.config import settings
from app.notifications.providers.base import EmailMessage, NotificationError, NotificationProvider

logger = logging.getLogger("notifications.smtp")


class SMTPNotificationProvider(NotificationProvider):
    """Notification provider that sends emails using SMTP."""

    def _build_smtp_options(self) -> dict[str, Any]:
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
        return smtp_options

    def send_email(self, message: EmailMessage) -> None:
        if not settings.emails_enabled:
            logger.warning(
                "Attempted to send email with SMTP provider but emails are disabled",
                extra={"provider": "smtp", "email_to": message.email_to},
            )
            return

        smtp_options = self._build_smtp_options()
        logger.info(
            "Sending email via SMTP provider",
            extra={
                "provider": "smtp",
                "email_to": message.email_to,
                "subject": message.subject,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
            },
        )
        try:
            email_message = emails.Message(
                subject=message.subject,
                html=message.html_content,
                mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
            )
            response = email_message.send(to=message.email_to, smtp=smtp_options)
            logger.info(
                "Email sent successfully via SMTP provider",
                extra={
                    "provider": "smtp",
                    "email_to": message.email_to,
                    "subject": message.subject,
                    "response": str(response),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Failed to send email via SMTP provider",
                extra={
                    "provider": "smtp",
                    "email_to": message.email_to,
                    "subject": message.subject,
                },
            )
            raise NotificationError("Error sending email via SMTP provider") from exc