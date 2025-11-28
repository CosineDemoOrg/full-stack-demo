import logging
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    @abstractmethod
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        raise NotImplementedError


class ConsoleEmailProvider(EmailProvider):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        logger.info(
            "Email sent",
            extra={
                "provider": "console",
                "email_to": email_to,
                "subject": subject,
                "html_length": len(html_content),
            },
        )


class SmtpEmailProvider(EmailProvider):
    def __init__(self) -> None:
        # Lazy import to keep provider isolated
        import emails  # type: ignore

        self._emails = emails

    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:
        if not settings.emails_enabled:
            logger.warning(
                "Tried to send email but emails are disabled",
                extra={
                    "provider": "smtp",
                    "email_to": email_to,
                },
            )
            return

        message = self._emails.Message(
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
            logger.info(
                "Email sent",
                extra={
                    "provider": "smtp",
                    "email_to": email_to,
                    "subject": subject,
                    "smtp_options": {
                        "host": settings.SMTP_HOST,
                        "port": settings.SMTP_PORT,
                        "tls": settings.SMTP_TLS,
                        "ssl": settings.SMTP_SSL,
                        "has_user": bool(settings.SMTP_USER),
                    },
                    "response": str(response),
                },
            )
        except Exception:
            logger.exception(
                "Error sending email",
                extra={
                    "provider": "smtp",
                    "email_to": email_to,
                    "subject": subject,
                },
            )


def get_email_provider() -> EmailProvider:
    provider_name = settings.EMAIL_PROVIDER.lower()
    if provider_name == "console":
        return ConsoleEmailProvider()
    if provider_name == "smtp":
        return SmtpEmailProvider()
    logger.warning(
        "Unknown email provider, falling back to console",
        extra={"provider": provider_name},
    )
    return ConsoleEmailProvider()