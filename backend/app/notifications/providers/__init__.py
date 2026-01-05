from __future__ import annotations

from functools import lru_cache
from typing import Literal

from app.core.config import settings
from app.notifications.providers.base import EmailMessage, NotificationProvider
from app.notifications.providers.console import ConsoleNotificationProvider
from app.notifications.providers.smtp import SMTPNotificationProvider

ProviderName = Literal["console", "smtp"]


@lru_cache(maxsize=1)
def get_notification_provider() -> NotificationProvider:
    provider_name: ProviderName = settings.NOTIFICATIONS_PROVIDER
    if provider_name == "smtp":
        return SMTPNotificationProvider()
    return ConsoleNotificationProvider()


__all__ = [
    "EmailMessage",
    "NotificationProvider",
    "get_notification_provider",
]