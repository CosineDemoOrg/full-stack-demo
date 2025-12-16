from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.notifications.provider import EmailMessage, NotificationProvider


@dataclass
class PasswordRecoveryContext:
    email_to: str
    email: str
    token: str


@dataclass
class WelcomeEmailContext:
    email_to: str
    username: str
    password: str


class NotificationService:
    def __init__(self, provider: NotificationProvider) -> None:
        self._provider = provider

    def send_password_recovery_email(self, context: PasswordRecoveryContext) -> None:
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Password recovery for user {context.email}"
        link = f"{settings.FRONTEND_HOST}/reset-password?token={context.token}"
        html_content = self._render_template(
            template_name="reset_password.html",
            context={
                "project_name": project_name,
                "username": context.email,
                "email": context.email_to,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": link,
            },
        )
        message = EmailMessage(
            email_to=context.email_to,
            subject=subject,
            html_content=html_content,
        )
        self._provider.send_email(message)

    def send_welcome_email(self, context: WelcomeEmailContext) -> None:
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - New account for user {context.username}"
        html_content = self._render_template(
            template_name="new_account.html",
            context={
                "project_name": project_name,
                "username": context.username,
                "password": context.password,
                "email": context.email_to,
                "link": settings.FRONTEND_HOST,
            },
        )
        message = EmailMessage(
            email_to=context.email_to,
            subject=subject,
            html_content=html_content,
        )
        self._provider.send_email(message)

    def generate_password_recovery_email_html(  # pragma: no cover - small wrapper
        self, context: PasswordRecoveryContext
    ) -> EmailMessage:
        """Generate the password recovery email without sending it."""
        project_name = settings.PROJECT_NAME
        subject = f"{project_name} - Password recovery for user {context.email}"
        link = f"{settings.FRONTEND_HOST}/reset-password?token={context.token}"
        html_content = self._render_template(
            template_name="reset_password.html",
            context={
                "project_name": project_name,
                "username": context.email,
                "email": context.email_to,
                "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
                "link": link,
            },
        )
        return EmailMessage(
            email_to=context.email_to,
            subject=subject,
            html_content=html_content,
        )

    @staticmethod
    def _render_template(template_name: str, context: dict[str, object]) -> str:
        from pathlib import Path

        from jinja2 import Template

        template_str = (
            Path(__file__).parent.parent
            / "email-templates"
            / "build"
            / template_name
        ).read_text()
        template = Template(template_str)
        return template.render(context)