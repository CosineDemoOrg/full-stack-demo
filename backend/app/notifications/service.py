from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from jinja2 import Template

from app.core.config import settings
from app.notifications.providers.base import get_provider


@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: Dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent.parent / "email-templates" / "build" / template_name
    ).read_text()
    html_content = Template(template_str).render(context)
    return html_content


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
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
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(email_to: str, username: str, password: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - New account for user {username}"
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
    return EmailData(html_content=html_content, subject=subject)


def send_email(*, email_to: str, subject: str = "", html_content: str = "") -> None:
    provider = get_provider(settings)
    try:
        provider.send(email_to=email_to, subject=subject, html_content=html_content)
    except Exception as e:
        # Structured error log; re-raise to surface errors in task runners/monitoring
        import logging

        logging.getLogger("notifications").error(
            "notification.error",
            extra={
                "provider": getattr(settings, "NOTIFICATIONS_PROVIDER", None),
                "to": email_to,
                "subject": subject,
                "error": str(e),
            },
        )
        raise