from __future__ import annotations

import logging

from app.notifications.providers.base import EmailMessage, NotificationProvider

logger = logging.getLogger("notifications.console")


class ConsoleNotificationProvider(NotificationProvider):
    """Notification provider that logs emails to the console."""

    def send_email(self, message: EmailMessage) -> None:
        logger.info(
            "Sending email via console provider",
            extra={
                "provider": "console",
                "email_to": message.email_to,
                "subject": message.subject,
            },
        )
        logger.info("Email content: %s", message.html_content)