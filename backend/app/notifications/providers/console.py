import json
import logging
from datetime import datetime, timezone

from app.notifications.provider import NotificationProvider

logger = logging.getLogger("notifications.console")


class ConsoleProvider(NotificationProvider):
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "provider": "console",
            "email_to": email_to,
            "subject": subject,
            "content_length": len(html_content),
        }
        logger.info(json.dumps(payload))