import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationError(RuntimeError):
    pass


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str


class EmailProvider(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        ...


class ConsoleEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> None:
        logger.info(
            "notification_email_console",
            extra={
                "event": "email.send.console",
                "to": message.to,
                "subject": message.subject,
                "provider": "console",
            },
        )


class SmtpEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> None:
        if not (settings.SMTP_HOST and settings.EMAILS_FROM_EMAIL):
            raise NotificationError("SMTP settings are not fully configured")

        mail = emails.Message(
            subject=message.subject,
            html=message.html,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options: dict[str, Any] = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD

        try:
            response = mail.send(to=message.to, smtp=smtp_options)
            logger.info(
                "notification_email_smtp",
                extra={
                    "event": "email.send.smtp",
                    "to": message.to,
                    "subject": message.subject,
                    "provider": "smtp",
                    "response": str(response),
                },
            )
        except Exception as exc:  # noqa: BLE001 - we want to wrap any provider error
            logger.exception(
                "notification_email_smtp_error",
                extra={"event": "email.send.smtp.error", "to": message.to, "subject": message.subject},
            )
            raise NotificationError("Failed to send SMTP email") from exc


def get_email_provider() -> EmailProvider:
    if settings.NOTIFICATIONS_PROVIDER == "smtp":
        return SmtpEmailProvider()
    return ConsoleEmailProvider()