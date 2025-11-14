import json
import logging

from .base import EmailMessage, NotificationProvider

logger = logging.getLogger("notifications.console")


class ConsoleProvider(NotificationProvider):
    def send(self, message: EmailMessage) -> None:
        logger.info(
            json.dumps(
                {
                    "provider": "console",
                    "event": "email_send",
                    "to": message.to,
                    "subject": message.subject,
                    "length_html": len(message.html),
                }
            )
        )