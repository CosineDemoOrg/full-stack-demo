from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger("app.notifications")


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str


class NotificationError(Exception):
    """Raised when sending a notification fails."""


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> None:  # pragma: no cover - protocol
        ...


@dataclass
class ConsoleEmailProvider:
    """Email provider that logs email contents instead of sending."""

    def send(self, message: EmailMessage) -> None:
        logger.info(
            "Console email provider: email prepared",
            extra={
                "provider": "console",
                "email_to": message.to,
                "subject": message.subject,
            },
        )
        logger.debug(
            "Console email provider: email body",
            extra={"email_to": message.to, "html": message.html},
        )


@dataclass
class SMTPEmailProvider:
    """Email provider that sends emails using SMTP."""

    host: str
    port: int
    from_name: str
    from_email: str
    user: str | None = None
    password: str | None = None
    use_tls: bool = True
    use_ssl: bool = False

    def send(self, message: EmailMessage) -> None:
        smtp_options: dict[str, object] = {
            "host": self.host,
            "port": self.port,
        }
        if self.use_tls:
            smtp_options["tls"] = True
        elif self.use_ssl:
            smtp_options["ssl"] = True
        if self.user:
            smtp_options["user"] = self.user
        if self.password:
            smtp_options["password"] = self.password

        try:
            mail = emails.Message(
                subject=message.subject,
                html=message.html,
                mail_from=(self.from_name, self.from_email),
            )
            response = mail.send(to=message.to, smtp=smtp_options)
            logger.info(
                "SMTP email sent",
                extra={
                    "provider": "smtp",
                    "email_to": message.to,
                    "subject": message.subject,
                    "response": str(response),
                },
            )
        except Exception as exc:  # pragma: no cover - error path
            logger.error(
                "SMTP email send failed",
                extra={
                    "provider": "smtp",
                    "email_to": message.to,
                    "subject": message.subject,
                },
                exc_info=exc,
            )
            raise NotificationError("Failed to send SMTP email") from exc


def get_email_provider() -> EmailProvider:
    """Return the configured email provider instance."""
    if settings.NOTIFICATIONS_PROVIDER == "console" or not settings.emails_enabled:
        return ConsoleEmailProvider()

    if not settings.SMTP_HOST or not settings.EMAILS_FROM_EMAIL:
        # Fallback to console if email settings are not fully configured.
        logger.warning(
            "SMTP provider selected but SMTP settings are incomplete, "
            "falling back to console provider",
            extra={"provider": settings.NOTIFICATIONS_PROVIDER},
        )
        return ConsoleEmailProvider()

    return SMTPEmailProvider(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        from_name=str(settings.EMAILS_FROM_NAME),
        from_email=str(settings.EMAILS_FROM_EMAIL),
        user=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=bool(settings.SMTP_TLS),
        use_ssl=bool(settings.SMTP_SSL),
    )