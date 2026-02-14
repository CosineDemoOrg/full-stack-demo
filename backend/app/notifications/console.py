import logging

from .base import NotificationProvider

logger = logging.getLogger(__name__)


class ConsoleProvider(NotificationProvider):
    def send_html(self, *, email_to: str, subject: str, html_content: str) -> None:
        payload = {"type": "email", "to": email_to, "subject": subject}
        try:
            logger.info("notification.dispatched", extra={"notification": payload})
            # Log the payload and content for local visibility
            logger.info(
                "notification.console",
                extra={"notification": payload, "html_length": len(html_content)},
            )
            logger.info(
                "notification.sent",
                extra={"notification": payload, "status": "success"},
            )
        except Exception as e:  # pragma: no cover
            logger.error(
                "notification.error",
                extra={"notification": payload, "error": str(e)},
            )
            raise