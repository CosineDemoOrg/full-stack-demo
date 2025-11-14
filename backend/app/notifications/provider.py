from __future__ import annotations

import logging
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger("notifications")


class EmailProvider(Protocol):
    def send(self, *, email_to: str, subject: str, html_content: str) -> None: ...


class ConsoleEmailProvider:
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "email.send",
            extra={
                "provider": "console",
                "to": email_to,
                "subject": subject,
                "length": len(html_content),
            },
        )


class SMTPEmailProvider:
    def __init__(self) -> None:
        # Validate minimal config up-front
        if not settings.SMTP_HOST:
            raise ValueError("SMTP_HOST must be set for SMTPEmailProvider")
        if not settings.EMAILS_FROM_EMAIL:
            raise ValueError("EMAILS_FROM_EMAIL must be set for SMTPEmailProvider")

    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        # Import locally to keep provider boundary small
        import emails  # type: ignore

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
            logger.info(
                "email.send",
                extra={
                    "provider": "smtp",
                    "to": email_to,
                    "subject": subject,
                    "response": str(response),
                },
            )
        except Exception as e:
            # Wrap and add context
            logger.exception(
                "email.error",
                extra={"provider": "smtp", "to": email_to, "subject": subject},
            )
            raise RuntimeError(f"SMTP provider failed to send email to {email_to}") from e