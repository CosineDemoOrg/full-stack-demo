import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from fastapi import BackgroundTasks
from jinja2 import Template

from app.core.config import settings
from app.utils import EmailData  # reuse dataclass
from .providers.base import EmailMessage, NotificationProvider
from .providers.console import ConsoleProvider
from .providers.smtp import SmtpProvider

logger = logging.getLogger("notifications.service")


def _render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent.parent / "email-templates" / "build" / template_name
    ).read_text()
    return Template(template_str).render(context)


@dataclass
class NotificationsService:
    provider: NotificationProvider

    def _send(self, to: str, subject: str, html: str) -> None:
        try:
            self.provider.send(EmailMessage(to=to, subject=subject, html=html))
        except Exception as e:  # noqa: BLE001
            logger.error(
                "notification_send_error",
                extra={"error": str(e), "to": to, "subject": subject},
            )
            raise

    def send_password_recovery(self, *, email_to: str, email: str, token: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Password recovery for user {email}"
        html = self.preview_password_recovery(email_to=email_to, email=email, token=token).html_content
        self._send(email_to, subject, html)

    def preview_password_recovery(self, *, email_to: str, email: str, token: str) -> EmailData:
        link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
        html = _render_email_template(
            template_name="reset_password.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": email,
                "email": email_to,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": link,
            },
        )
        subject = f"{settings.PROJECT_NAME} - Password recovery for user {email}"
        return EmailData(html_content=html, subject=subject)

    def send_welcome(self, *, email_to: str, username: str, password: str) -> None:
        subject = f"{settings.PROJECT_NAME} - New account for user {username}"
        html = _render_email_template(
            template_name="new_account.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": username,
                "password": password,
                "email": email_to,
                "link": settings.FRONTEND_HOST,
            },
        )
        self._send(email_to, subject, html)

    def send_test(self, *, email_to: str) -> EmailData:
        subject = f"{settings.PROJECT_NAME} - Test email"
        html = _render_email_template(
            template_name="test_email.html",
            context={"project_name": settings.PROJECT_NAME, "email": email_to},
        )
        self._send(email_to, subject, html)
        return EmailData(html_content=html, subject=subject)


def get_notifications_service() -> NotificationsService:
    provider_choice: Literal["console", "smtp"] = getattr(
        settings, "NOTIFICATIONS_PROVIDER", "console"
    )
    if provider_choice == "smtp":
        provider = SmtpProvider()
    else:
        provider = ConsoleProvider()
    return NotificationsService(provider=provider)


def schedule_background_notifications(
    tasks: BackgroundTasks, func: Callable[[], None]
) -> None:
    tasks.add_task(func)