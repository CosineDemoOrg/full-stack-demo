from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.notifications.providers import EmailMessage, get_notification_provider
from app.utils import render_email_template


@dataclass(slots=True)
class EmailData:
    html_content: str
    subject: str


def _build_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"project_name": settings.PROJECT_NAME, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def _build_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
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


def _build_new_account_email(
    email_to: str, username: str, password: str
) -> EmailData:
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


def send_test_email(email_to: str) -> None:
    email_data = _build_test_email(email_to=email_to)
    provider = get_notification_provider()
    provider.send_email(
        EmailMessage(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    )


def send_password_recovery_email(email_to: str, email: str, token: str) -> None:
    email_data = _build_reset_password_email(
        email_to=email_to, email=email, token=token
    )
    provider = get_notification_provider()
    provider.send_email(
        EmailMessage(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    )


def send_welcome_email(email_to: str, username: str, password: str) -> None:
    email_data = _build_new_account_email(
        email_to=email_to, username=username, password=password
    )
    provider = get_notification_provider()
    provider.send_email(
        EmailMessage(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    )