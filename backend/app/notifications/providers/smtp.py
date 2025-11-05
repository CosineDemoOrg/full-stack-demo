import logging

import emails  # type: ignore

from app.core.config import settings
from app.notifications.provider import EmailMessage, NotificationProvider

logger = logging.getLogger("notifications.smtp")


class SMTPProvider(NotificationProvider):
    def send_email(self, message: EmailMessage) -> None:
        # Build message
        email_message = emails.Message(
            subject=message.subject,
            html=message.html_content,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options: dict[str, object] = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD

        try:
            response = email_message.send(to=message.to, smtp=smtp_options)
            logger.info(
                "notification_email_sent",
                extra={
                    "provider": "smtp",
                    "to": message.to,
                    "subject": message.subject,
                    "response": str(response),
                },
            )
        except Exception as exc:  # noqa: BLE001 - we want to wrap and log any send error
            logger.error(
                "notification_email_error",
                extra={"provider": "smtp", "to": message.to, "subject": message.subject},
            )
            # Re-raise to allow upstream handling if needed
            raise