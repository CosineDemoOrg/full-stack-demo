import logging

import emails  # type: ignore

from app.core.config import settings
from .base import NotificationProvider

logger = logging.getLogger(__name__)


class SMTPProvider(NotificationProvider):
    def send_html(self, *, email_to: str, subject: str, html_content: str) -> None:
        if not settings.emails_enabled:
            raise RuntimeError("SMTP provider is not configured")

        message = emails.Message(
            subject=subject,
            html=html_content,
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

        payload = {"type": "email", "to": email_to, "subject": subject, "provider": "smtp"}
        try:
            logger.info("notification.dispatched", extra={"notification": payload})
            response = message.send(to=email_to, smtp=smtp_options)
            logger.info(
                "notification.sent",
                extra={"notification": payload, "status": "success", "response": str(response)},
            )
        except Exception as e:
            logger.error(
                "notification.error",
                extra={"notification": payload, "error": str(e)},
            )
            raise