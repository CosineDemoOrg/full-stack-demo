import logging

from app.core.config import settings
from app.notifications.models import EmailMessage
from app.notifications.providers import ConsoleEmailProvider, EmailProvider, SmtpEmailProvider
from app.utils import (
    EmailData,
    generate_new_account_email,
    generate_reset_password_email,
)

logger = logging.getLogger(__name__)


def get_email_provider() -> EmailProvider:
    if settings.NOTIFICATIONS_PROVIDER == "console":
        return ConsoleEmailProvider()
    if settings.NOTIFICATIONS_PROVIDER == "smtp":
        return SmtpEmailProvider()
    logger.warning(
        "Unknown NOTIFICATIONS_PROVIDER, falling back to console",
        extra={"provider": settings.NOTIFICATIONS_PROVIDER},
    )
    return ConsoleEmailProvider()


def _email_data_to_message(email_to: str, email_data: EmailData) -> EmailMessage:
    return EmailMessage(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


def send_welcome_email(*, email_to: str, username: str, password: str) -> None:
    if not settings.emails_enabled:
        logger.info(
            "Emails are disabled, skipping welcome email",
            extra={"email_to": email_to},
        )
        return

    email_data = generate_new_account_email(
        email_to=email_to,
        username=username,
        password=password,
    )
    message = _email_data_to_message(email_to=email_to, email_data=email_data)
    provider = get_email_provider()
    try:
        provider.send(message)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(
            "Failed to send welcome email",
            extra={"email_to": email_to, "error": str(exc)},
        )


def send_password_recovery_email(*, email_to: str, email: str, token: str) -> None:
    if not settings.emails_enabled:
        logger.info(
            "Emails are disabled, skipping password recovery email",
            extra={"email_to": email_to},
        )
        return

    email_data = generate_reset_password_email(
        email_to=email_to,
        email=email,
        token=token,
    )
    message = _email_data_to_message(email_to=email_to, email_data=email_data)
    provider = get_email_provider()
    try:
        provider.send(message)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception(
            "Failed to send password recovery email",
            extra={"email_to": email_to, "error": str(exc)},
        )