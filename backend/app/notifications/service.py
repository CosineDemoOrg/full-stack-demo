import logging
from typing import Literal

from app.core.config import settings
from app.utils import render_email_template
from .base import Notification
from .console import ConsoleProvider
from .smtp import SMTPProvider

logger = logging.getLogger("notifications")


def get_provider(name: Literal["console", "smtp"]) -> ConsoleProvider | SMTPProvider:
    if name == "smtp":
        return SMTPProvider()
    return ConsoleProvider()


class Notifier:
    def __init__(self) -> None:
        provider_name: Literal["console", "smtp"] = settings.NOTIFICATIONS_PROVIDER
        self.provider = get_provider(provider_name)
        logger.info("notifications.init", extra={"provider": provider_name})

    def send_welcome(self, *, email_to: str, username: str, password: str) -> None:
        subject = f"{settings.PROJECT_NAME} - New account for user {username}"
        html = render_email_template(
            template_name="new_account.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": username,
                "password": password,
                "email": email_to,
                "link": settings.FRONTEND_HOST,
            },
        )
        self.provider.send(Notification(to=email_to, subject=subject, html=html))

    def send_password_recovery(self, *, email_to: str, email: str, token: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Password recovery for user {email}"
        link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
        html = render_email_template(
            template_name="reset_password.html",
            context={
                "project_name": settings.PROJECT_NAME,
                "username": email,
                "email": email_to,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": link,
            },
        )
        self.provider.send(Notification(to=email_to, subject=subject, html=html))


notifier = Notifier()