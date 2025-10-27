from __future__ import annotations

from typing import Literal

from app.core.config import settings
from app.notifications.base import NotificationProvider
from app.notifications.providers.console import ConsoleProvider
from app.notifications.providers.smtp import SMTPProvider


def get_provider() -> NotificationProvider:
    provider_name: Literal["console", "smtp"] = settings.notifications_provider
    if provider_name == "smtp":
        return SMTPProvider()
    return ConsoleProvider()