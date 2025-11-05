import logging

from app.notifications.provider import EmailMessage, NotificationProvider

logger = logging.getLogger("notifications.console")


class ConsoleProvider(NotificationProvider):
    def send_email(self, message: EmailMessage) -> None:
        logger.info(
            "notification_email_sent",
            extra={
                "provider": "console",
                "to": message.to,
                "subject": message.subject,
                "content_length": len(message.html_content),
            },
        )
        # Also print to console for local dev visibility
        print(f"[ConsoleProvider] To: {message.to} | Subject: {message.subject}")