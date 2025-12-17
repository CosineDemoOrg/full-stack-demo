from __future__ import annotations

import logging

from app.utils import (
    EmailData,
    generate_new_account_email,
    generate_reset_password_email,
)

from .providers import EmailMessage, EmailProvider, NotificationError, get_email_provider

logger = logging.getLogger("app.notifications")


class NotificationService:
    """Service responsible for higher-level notification flows."""

    def __init__(self, provider: EmailProvider) -> None:
        self.provider = provider

    def _send(self, notification_type: str, message: EmailMessage) -> None:
        try:
            self.provider.send(message)
        except Exception as exc:  # pragma: no cover - error path
            logger.error(
                "Failed to send notification",
                extra={
                    "notification_type": notification_type,
                    "email_to": message.to,
                    "provider": type(self.provider).__name__,
                },
                exc_info=exc,
            )
            raise NotificationError(
                f"Failed to send {notification_type} notification"
            ) from exc

    def send_password_recovery_email(
        self,
        *,
        email_to: str,
        email: str,
        token: str,
    ) -> None:
        """Send password recovery email."""
        email_data: EmailData = generate_reset_password_email(
            email_to=email_to,
            email=email,
            token=token,
        )
        message = EmailMessage(
            to=email_to,
            subject=email_data.subject,
            html=email_data.html_content,
        )
        self._send("password_recovery", message)

    def send_welcome_email(
        self,
        *,
        email_to: str,
        username: str,
        password: str,
    ) -> None:
        """Send welcome email for a new account."""
        email_data: EmailData = generate_new_account_email(
            email_to=email_to,
            username=username,
            password=password,
        )
        message = EmailMessage(
            to=email_to,
            subject=email_data.subject,
            html=email_data.html_content,
        )
        self._send("welcome", message)


def get_notification_service() -> NotificationService:
    """Factory used by FastAPI endpoints to get a notification service."""
    provider = get_email_provider()
    return NotificationService(provider)