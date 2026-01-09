import logging
from typing import Protocol, runtime_checkable

from app.core.config import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class NotificationProvider(Protocol):
    def send_email(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover - Protocol
        ...


def get_notification_provider() -> NotificationProvider:
    """
    Return the configured notification provider based on settings.

    The provider is selected via settings.NOTIFICATIONS_PROVIDER.
    """
    from app.notifications.providers import ConsoleNotificationProvider, SMTPNotificationProvider

    provider_name = settings.NOTIFICATIONS_PROVIDER

    if provider_name == "console":
        logger.info("Using ConsoleNotificationProvider for notifications")
        return ConsoleNotificationProvider()

    if provider_name == "smtp":
        logger.info("Using SMTPNotificationProvider for notifications")
        return SMTPNotificationProvider()

    logger.warning(
        "Unknown NOTIFICATIONS_PROVIDER '%s', falling back to ConsoleNotificationProvider",
        provider_name,
    )
    return ConsoleNotificationProvider()