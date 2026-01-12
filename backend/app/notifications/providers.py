import logging
from abc import ABC, abstractmethod

import emails  # type: ignore

from app.core.config import settings
from app.notifications.models import EmailMessage

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> None:
        logger.info(
            "Sending email via console provider",
            extra={
                "destination": message.email_to,
                "subject": message.subject,
                "provider": "console",
            },
        )
        print(f"[EMAIL] To: {message.email_to} | Subject: {message.subject}")
        print(message.html_content)


class SmtpEmailProvider(EmailProvider):
    def send(self, message: EmailMessage) -> None:
        assert settings.emails_enabled, "no provided configuration for email variables"

        logger.info(
            "Sending email via SMTP provider",
            extra={
                "destination": message.email_to,
                "subject": message.subject,
                "provider": "smtp",
                "host": settings.SMTP_HOST,
                "port": settings.SMTP_PORT,
            },
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

        message_to_send = emails.Message(
            subject=message.subject,
            html=message.html_content,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        response = message_to_send.send(to=message.email_to, smtp=smtp_options)
        logger.info(
            "Email send completed",
            extra={
                "destination": message.email_to,
                "subject": message.subject,
                "provider": "smtp",
                "result": str(response),
            },
        )