import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Template

from app.core.config import settings
from app.notifications.providers import (
    ConsoleProvider,
    NotificationError,
    NotificationProvider,
    SmtpProvider,
)

logger = logging.getLogger("app.notifications")


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent.parent
        / "email-templates"
        / "build"
        / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


@dataclass
class NotificationService:
    provider: NotificationProvider

    def send_test_email(self, *, email_to: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Test email"
        html_content = render_email_template(
            template_name="test_email.html",
            context={"project_name": settings.PROJECT_NAME, "email": email_to},
        )
        self._send(email_to=email_to, subject=subject, html_content=html_content)

    def send_welcome_email(self, *, email_to: str, username: str, password: str) -> None:
        subject = f"{settings.PROJECT_NAME} - New account for user {username}"
        html_content = render_email_template(
            template_name="new_account.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": username,
                "password": password,
                "email": email_to,
                "link": settings.FRONTEND_HOST,
            },
        )
        self._send(email_to=email_to, subject=subject, html_content=html_content)

    def send_password_recovery(self, *, email_to: str, email: str, token: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Password recovery for user {email}"
        link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
        html_content = render_email_template(
            template_name="reset_password.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": email,
                "email": email_to,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": link,
            },
        )
        self._send(email_to=email_to, subject=subject, html_content=html_content)

    def _send(self, *, email_to: str, subject: str, html_content: str) -> None:
        try:
            self.provider.send_email(
                email_to=email_to, subject=subject, html_content=html_content
            )
        except NotificationError:
            # Already logged at provider level
            raise
        except Exception as e:
            logger.exception(
                "Unhandled error sending notification",
                extra={"channel": "email", "email_to": email_to, "subject": subject},
            )
            raise NotificationError(str(e)) from e


def get_notification_service() -> NotificationService:
    if settings.NOTIFICATIONS_PROVIDER == "smtp":
        provider: NotificationProvider = SmtpProvider()
    else:
        provider = ConsoleProvider()
    return NotificationService(provider=provider)