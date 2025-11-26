import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import emails  # type: ignore
from jinja2 import Template

from app.core.config import settings
from app.utils import (
    EmailData,
    generate_new_account_email,
    generate_password_reset_token,
    generate_reset_password_email,
)

logger = logging.getLogger("app.notifications.email")


@runtime_checkable
class EmailProvider(Protocol):
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover - protocol definition
        ...


class NotificationError(Exception):
    pass


class ConsoleEmailProvider:
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "email.sent",
            extra={
                "provider": "console",
                "to": email_to,
                "subject": subject,
                "content_preview": html_content[:120],
            },
        )


class SmtpEmailProvider:
    def __init__(self) -> None:
        self._from_email = settings.EMAILS_FROM_EMAIL
        self._from_name = settings.EMAILS_FROM_NAME
        self._host = settings.SMTP_HOST
        self._port = settings.SMTP_PORT
        self._user = settings.SMTP_USER
        self._password = settings.SMTP_PASSWORD
        self._use_tls = settings.SMTP_TLS
        self._use_ssl = settings.SMTP_SSL

    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        if not settings.emails_enabled:
            logger.warning(
                "email.disabled",
                extra={
                    "provider": "smtp",
                    "reason": "emails not enabled in settings",
                    "to": email_to,
                    "subject": subject,
                },
            )
            return

        message = emails.Message(
            subject=subject,
            html=html_content,
            mail_from=(self._from_name, self._from_email),
        )
        smtp_options: dict[str, Any] = {"host": self._host, "port": self._port}
        if self._use_tls:
            smtp_options["tls"] = True
        elif self._use_ssl:
            smtp_options["ssl"] = True
        if self._user:
            smtp_options["user"] = self._user
        if self._password:
            smtp_options["password"] = self._password

        try:
            response = message.send(to=email_to, smtp=smtp_options)
        except Exception as exc:  # pragma: no cover - exercised indirectly
            logger.exception(
                "email.send_error",
                extra={
                    "provider": "smtp",
                    "to": email_to,
                    "subject": subject,
                },
            )
            raise NotificationError("Error sending email") from exc

        logger.info(
            "email.sent",
            extra={
                "provider": "smtp",
                "to": email_to,
                "subject": subject,
                "response": str(response),
            },
        )


_email_provider: EmailProvider | None = None


def get_email_provider() -> EmailProvider:
    global _email_provider
    if _email_provider is None:
        if settings.NOTIFICATIONS_EMAIL_PROVIDER == "console":
            _email_provider = ConsoleEmailProvider()
        elif settings.NOTIFICATIONS_EMAIL_PROVIDER == "smtp":
            _email_provider = SmtpEmailProvider()
        else:
            raise ValueError(
                f"Unknown NOTIFICATIONS_EMAIL_PROVIDER: {settings.NOTIFICATIONS_EMAIL_PROVIDER}"
            )
    return _email_provider


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parents[1] / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    provider = get_email_provider()
    provider.send(email_to=email_to, subject=subject, html_content=html_content)


def generate_test_email(email_to: str) -> EmailData:
    subject = f"{settings.PROJECT_NAME} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def send_password_recovery_email(*, email: str) -> None:
    token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=email,
        email=email,
        token=token,
    )
    provider = get_email_provider()
    provider.send(
        email_to=email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


def send_welcome_email(*, email: str, password: str) -> None:
    email_data = generate_new_account_email(
        email_to=email,
        username=email,
        password=password,
    )
    provider = get_email_provider()
    provider.send(
        email_to=email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )