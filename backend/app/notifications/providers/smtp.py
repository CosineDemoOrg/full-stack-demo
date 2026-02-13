import logging

import emails  # type: ignore

from app.core.config import settings
from app.notifications.provider import NotificationProvider

logger = logging.getLogger("notifications.smtp")


class SmtpProvider(NotificationProvider):
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        if not settings.emails_enabled:
            raise RuntimeError("SMTP settings not configured")

        message = emails.Message(
            subject=subject,
            html=html_content,
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

        try:
            response = message.send(to=email_to, smtp=smtp_options)
            logger.info("SMTP send ok: %s", response)
        except Exception as exc:  # noqa: BLE001 - we want to bubble up but log structured context
            logger.error(
                "SMTP send failed",
                extra={
                    "provider": "smtp",
                    "email_to": email_to,
                    "subject": subject,
                },
            )
            raise