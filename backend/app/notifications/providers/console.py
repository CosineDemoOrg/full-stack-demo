import logging
from typing import Any

from .base import NotificationProvider

logger = logging.getLogger("notifications.console")


class ConsoleProvider(NotificationProvider):
    def __init__(self, *, settings: Any) -> None:
        self.settings = settings

    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        # Structured logging
        logger.info(
            "notification.send",
            extra={
                "provider": "console",
                "to": email_to,
                "subject": subject,
                "project": getattr(self.settings, "PROJECT_NAME", None),
            },
        )
        # Also log the content for local dev visibility
        logger.debug("notification.content", extra={"html": html_content})