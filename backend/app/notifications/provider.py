import logging
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger("app.notifications")


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str


@runtime_checkable
class NotificationProvider(Protocol):
    def send_email(self, message: EmailMessage) -> None:  # pragma: no cover - Protocol
        ...


class ConsoleNotificationProvider:
    def send_email(self, message: EmailMessage) -> None:
        logger.info(
            "notification_email_scheduled",
            extra={
                "channel": "console",
                "to": message.to,
                "subject": message.subject,
            },
        )
        # Log the full HTML at debug level to avoid noise in normal logs
        logger.debug(
            "notification_email_html",
            extra={"to": message.to, "subject": message.subject, "html": message.html},
        )


class SMTPNotificationProvider:
    def send_email(self, message: EmailMessage) -> None:
        assert (
            settings.emails_enabled
        ), "no provided configuration for email variables (SMTP)"
        msg = emails.Message(
            subject=message.subject,
            html=message.html,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options: dict[str, object] = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD
        response = msg.send(to=message.to, smtp=smtp_options)
        logger.info(
            "notification_email_sent",
            extra={
                "channel": "smtp",
                "to": message.to,
                "subject": message.subject,
                "response": str(response),
            },
        )


def get_provider() -> NotificationProvider:
    if settings.NOTIFICATIONS_PROVIDER == "smtp":
        return SMTPNotificationProvider()
    # default
    return ConsoleNotificationProvider()