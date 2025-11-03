import logging

import emails  # type: ignore

from app.core.config import settings
from .base import Notification, NotificationError, NotificationProvider

logger = logging.getLogger("notifications")


class SMTPProvider(NotificationProvider):
    def send(self, notification: Notification) -> None:
        if not settings.emails_enabled:
            logger.warning(
                "notification.skipped",
                extra={
                    "provider": "smtp",
                    "reason": "emails_disabled",
                    "to": notification.to,
                    "subject": notification.subject,
                },
            )
            return

        message = emails.Message(
            subject=notification.subject,
            html=notification.html,
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
            response = message.send(to=notification.to, smtp=smtp_options)
            logger.info(
                "notification.send",
                extra={
                    "provider": "smtp",
                    "to": notification.to,
                    "subject": notification.subject,
                    "response": str(response),
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.error(
                "notification.error",
                extra={
                    "provider": "smtp",
                    "to": notification.to,
                    "subject": notification.subject,
                    "error": type(e).__name__,
                    "message": str(e),
                },
            )
            raise NotificationError("Error sending SMTP notification", cause=e)