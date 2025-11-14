import logging
from typing import Any

import emails  # type: ignore

from app.core.config import settings
from .base import EmailMessage, NotificationProvider

logger = logging.getLogger("notifications.smtp")


class SmtpProvider(NotificationProvider):
    def __init__(self) -> None:
        if not settings.emails_enabled:
            raise RuntimeError("SMTP is not configured but SmtpProvider was selected")

    def _smtp_options(self) -> dict[str, Any]:
        opts: dict[str, Any] = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            opts["tls"] = True
        elif settings.SMTP_SSL:
            opts["ssl"] = True
        if settings.SMTP_USER:
            opts["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            opts["password"] = settings.SMTP_PASSWORD
        return opts

    def send(self, message: EmailMessage) -> None:
        msg = emails.Message(
            subject=message.subject,
            html=message.html,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        response = msg.send(to=message.to, smtp=self._smtp_options())
        logger.info("smtp_send_result=%s", response)