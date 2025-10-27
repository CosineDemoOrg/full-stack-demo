from __future__ import annotations

import logging

from app.notifications.base import NotificationProvider, log_send_result

logger = logging.getLogger(__name__)


class ConsoleProvider(NotificationProvider):
    def send(self, *, email_to: str, subject: str, html_content: str) -> dict[str, str]:
        # Log the email content to console instead of sending
        logger.info(
            "console_notification email_to=%s subject=%s html_length=%d",
            email_to,
            subject,
            len(html_content),
        )
        result = {"status": "logged"}
        log_send_result("console", email_to=email_to, subject=subject, result=result)
        return result