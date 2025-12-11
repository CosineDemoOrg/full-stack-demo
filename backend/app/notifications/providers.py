import logging
from dataclasses import dataclass
from typing import Any

import emails  # type: ignore

from app.core.config import settings
from app.notifications.exceptions import NotificationError

logger = logging.getLogger(__name__)


@dataclass
class _SMTPConfig:
    host: str
    port: int
    tls: bool
    ssl: bool
    user: str | None
    password: str | None
    from_name: str
    from_email: str


class ConsoleNotificationProvider:
    """
    Notification provider that logs emails to the console.

    Useful for local development and testing without an SMTP server.
    """

    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        payload: dict[str, Any] = {
            "provider": "console",
            "email_to": email_to,
            "subject": subject,
            "html_length": len(html_content),
        }
        logger.info("notification_email_console", extra=payload)


class SMTPNotificationProvider:
    """
    Notification provider that sends emails via SMTP using the `emails` library.
    """

    def __init__(self) -> None:
        if not settings.emails_enabled:
            raise NotificationError("SMTPNotificationProvider requires email settings")

        if not settings.SMTP_HOST:
            raise NotificationError("SMTP_HOST must be set for SMTPNotificationProvider")

        self.config = _SMTPConfig(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            tls=settings.SMTP_TLS,
            ssl=settings.SMTP_SSL,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            from_name=str(settings.EMAILS_FROM_NAME),
            from_email=str(settings.EMAILS_FROM_EMAIL),
        )

    def _smtp_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {"host": self.config.host, "port": self.config.port}
        if self.config.tls:
            options["tls"] = True
        elif self.config.ssl:
            options["ssl"] = True
        if self.config.user:
            options["user"] = self.config.user
        if self.config.password:
            options["password"] = self.config.password
        return options

    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        payload: dict[str, Any] = {
            "provider": "smtp",
            "email_to": email_to,
            "subject": subject,
            "html_length": len(html_content),
            "smtp_host": self.config.host,
            "smtp_port": self.config.port,
        }
        try:
            message = emails.Message(
                subject=subject,
                html=html_content,
                mail_from=(self.config.from_name, self.config.from_email),
            )
            response = message.send(to=email_to, smtp=self._smtp_options())
            logger.info("notification_email_smtp_success", extra={**payload, "response": str(response)})
        except Exception as exc:  # pragma: no cover - error path
            logger.error("notification_email_smtp_error", extra={**payload, "error": repr(exc)})
            raise NotificationError("Error sending email via SMTP") from exc