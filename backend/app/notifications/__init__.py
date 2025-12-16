from functools import lru_cache
from typing import Literal

from app.core.config import settings

from .provider import (
    ConsoleNotificationProvider,
    NotificationProvider,
    SMTPNotificationProvider,
)


ProviderName = Literal["console", "smtp"]


@lru_cache(maxsize=1)
def get_notification_provider() -> NotificationProvider:
    provider_name: ProviderName = getattr(
        settings, "NOTIFICATIONS_PROVIDER", "console"
    )  # type: ignore[assignment]
    if provider_name == "smtp":
        return SMTPNotificationProvider()
    return ConsoleNotificationProvider()