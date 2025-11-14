from __future__ import annotations

import logging
from typing import Literal

from app.core.config import settings
from app.notifications.emails import (
    EmailData,
    build_new_account_email,
    build_reset_password_email,
    build_test_email,
)
from app.notifications.provider import ConsoleEmailProvider, EmailProvider, SMTPEmailProvider

logger = logging.getLogger("notifications")


def get_provider(kind: Literal["console", "smtp"]) -> EmailProvider:
    if kind == "console":
        return ConsoleEmailProvider()
    elif kind == "smtp":
        return SMTPEmailProvider()
    raise ValueError(f"Unknown notifications provider: {kind}")


class NotificationsService:
    def __init__(self, provider: EmailProvider | None = None) -> None:
        self.provider = provider or get_provider(settings.NOTIFICATIONS_PROVIDER)

    def send_email_data(self, email_to: str, email_data: EmailData) -> None:
        self.provider.send(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    def send_test_email(self, *, email_to: str) -> None:
        self.send_email_data(email_to, build_test_email(email_to))

    def send_password_recovery(self, *, email_to: str, email: str, token: str) -> None:
        self.send_email_data(email_to, build_reset_password_email(email_to, email, token))

    def send_welcome(self, *, email_to: str, username: str, password: str) -> None:
        self.send_email_data(email_to, build_new_account_email(email_to, username, password))


# Singleton for importers
notifications_service = NotificationsService()