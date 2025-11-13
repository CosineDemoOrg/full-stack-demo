import logging
from dataclasses import dataclass
from typing import Protocol

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger("app.notifications")


class NotificationError(Exception):
    pass


class NotificationProvider(Protocol):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None: ...


@dataclass
class ConsoleProvider:
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "Sending email (console)",
            extra={
                "channel": "email",
                "provider": "console",
                "email_to": email_to,
                "subject": subject,
                "length": len(html_content),
            },
        )


@dataclass
class SmtpProvider:
    def _smtp_options(self) -> dict:
        if not settings.emails_enabled:
            raise NotificationError("SMTP not configured (emails not enabled)")
        smtp_options: dict = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD
        return smtp_options

    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        try:
            message = emails.Message(
                subject=subject,
                html=html_content,
                mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
            )
            response = message.send(to=email_to, smtp=self._smtp_options())
            logger.info(
                "Email sent via SMTP",
                extra={
                    "channel": "email",
                    "provider": "smtp",
                    "email_to": email_to,
                    "subject": subject,
                    "response": str(response),
                },
            )
        except Exception as e:
            logger.exception(
                "Error sending email via SMTP",
                extra={"channel": "email", "provider": "smtp", "email_to": email_to},
            )
            raise NotificationError(str(e)) from e