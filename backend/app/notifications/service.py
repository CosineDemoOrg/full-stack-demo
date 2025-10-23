import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings
from app.notifications.provider import EmailMessage, EmailProvider, get_email_provider

logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    html_content: str
    subject: str


def _render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (Path(__file__).parent.parent / "email-templates" / "build" / template_name).read_text()
    html_content = Template(template_str).render(context)
    return html_content


class NotificationService:
    def __init__(self, provider: EmailProvider | None = None) -> None:
        self.provider = provider or get_email_provider()

    def send_test_email(self, *, email_to: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Test email"
        html_content = _render_email_template(
            template_name="test_email.html",
            context={"project_name": settings.PROJECT_NAME, "email": email_to},
        )
        self._send(email_to=email_to, subject=subject, html_content=html_content)

    def send_welcome_email(self, *, email_to: str, username: str, password: str) -> None:
        subject = f"{settings.PROJECT_NAME} - New account for user {username}"
        html_content = _render_email_template(
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

    def send_password_reset_email(self, *, email_to: str, email: str, token: str) -> None:
        subject = f"{settings.PROJECT_NAME} - Password recovery for user {email}"
        link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
        html_content = _render_email_template(
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
        message = EmailMessage(to=email_to, subject=subject, html=html_content)
        logger.info(
            "notification_email_send",
            extra={"event": "email.send", "to": email_to, "subject": subject, "provider": type(self.provider).__name__},
        )
        self.provider.send(message)


# Keep token utilities here to avoid circular imports with legacy utils
def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None