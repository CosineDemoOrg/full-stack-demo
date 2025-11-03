import logging
from typing import Any, Dict

import emails  # type: ignore

logger = logging.getLogger("notifications.smtp")


class SMTPProvider:
    def __init__(self, *, settings: Any) -> None:
        self.settings = settings

    def _smtp_options(self) -> Dict[str, Any]:
        opts: Dict[str, Any] = {
            "host": self.settings.SMTP_HOST,
            "port": self.settings.SMTP_PORT,
        }
        if self.settings.SMTP_TLS:
            opts["tls"] = True
        elif self.settings.SMTP_SSL:
            opts["ssl"] = True
        if self.settings.SMTP_USER:
            opts["user"] = self.settings.SMTP_USER
        if self.settings.SMTP_PASSWORD:
            opts["password"] = self.settings.SMTP_PASSWORD
        return opts

    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        assert self.settings.emails_enabled, "emails not enabled in settings"
        message = emails.Message(
            subject=subject,
            html=html_content,
            mail_from=(self.settings.EMAILS_FROM_NAME, self.settings.EMAILS_FROM_EMAIL),
        )
        smtp_options = self._smtp_options()
        response = message.send(to=email_to, smtp=smtp_options)
        logger.info(
            "notification.send",
            extra={
                "provider": "smtp",
                "to": email_to,
                "subject": subject,
                "response": str(response),
                "project": getattr(self.settings, "PROJECT_NAME", None),
            },
        )