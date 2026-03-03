import logging
from abc import ABC, abstractmethod

import emails  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationSendError(RuntimeError):
    """Raised when sending a notification fails."""


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        raise NotImplementedError


class ConsoleNotificationProvider(BaseNotificationProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            {
                "event": "notification.send.console",
                "status": "success",
                "provider": "console",
                "email_to": email_to,
                "subject": subject,
                "html_length": len(html_content),
            }
        )


class SmtpNotificationProvider(BaseNotificationProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        if not settings.emails_enabled:
            raise NotificationSendError("Email settings are not configured")

        message = emails.Message(
            subject=subject,
            html=html_content,
            mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
        )
        smtp_options: dict[str, object] = {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
        }
        if settings.SMTP_TLS:
            smtp_options["tls"] = True
        elif settings.SMTP_SSL:
            smtp_options["ssl"] = True
        if settings.SMTP_USER:
            smtp_options["user"] = settings.SMTP_USER
        if settings.SMTP_PASSWORD:
            smtp_options["password"] = settings.SMTP_PASSWORD
        try:
            response = message.send(to=email_to, smtp=smtp_options)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Error sending email with SMTP provider",
                extra={
                    "event": "notification.send.smtp",
                    "status": "error",
                    "provider": "smtp",
                    "email_to": email_to,
                    "subject": subject,
                },
            )
            raise NotificationSendError("Error sending email via SMTP") from exc

        logger.info(
            {
                "event": "notification.send.smtp",
                "status": "success",
                "provider": "smtp",
                "email_to": email_to,
                "subject": subject,
                "response": str(response),
            }
        )


def get_provider() -> BaseNotificationProvider:
    provider_name = settings.NOTIFICATIONS_PROVIDER
    if provider_name == "console":
        return ConsoleNotificationProvider()
    if provider_name == "smtp":
        return SmtpNotificationProvider()
    raise ValueError(f"Unsupported notifications provider: {provider_name}")