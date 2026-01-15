import logging

from .base import Notification, NotificationProvider

logger = logging.getLogger("notifications")


class ConsoleProvider(NotificationProvider):
    def send(self, notification: Notification) -> None:
        # Structured logging
        logger.info(
            "notification.send",
            extra={
                "provider": "console",
                "to": notification.to,
                "subject": notification.subject,
                "bytes": len(notification.html),
            },
        )