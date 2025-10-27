from __future__ import annotations

from typing import Any

import emails  # type: ignore

from app.core.config import settings
from app.notifications.base import NotificationProvider, log_send_result


class SMTPProvider(NotificationProvider):
    def send(self, *, email_to: str, subject: str, html_content: str) -> Any:
        assert settings.emails_enabled, "no provided configuration for email variables"
        message = emails.Message(
            subject=subject,
            html=html_content,
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
        response = message.send(to=email_to, smtp=smtp_options)
        log_send_result("smtp", email_to=email_to, subject=subject, result=response)
        return response